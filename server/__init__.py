import cherrypy
import json
import os

from girder.api import access, rest
from girder.api.describe import Description
from girder.constants import AccessType

_script_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            'climos_script.py')
with open(_script_file) as f:
    _climos_script = f.read()


class Climos(rest.Resource):
    def __init__(self):
        self.resourceName = 'climos'
        self.route('POST', (), self.runClimos)

    @access.user
    @rest.loadmodel(map={'inputFolderId': 'inFolder'}, model='folder',
                    level=AccessType.READ)
    @rest.loadmodel(map={'outputFolderId': 'outFolder'}, model='folder',
                    level=AccessType.WRITE)
    def runClimos(self, inFolder, outFolder, params):
        self.requireParams(('seasons', 'vars', 'outputFilename'), params)

        user = self.getCurrentUser()
        urlParts = rest.getUrlParts()
        apiUrl = rest.getApiUrl()
        jobModel = self.model('job', 'jobs')
        job = jobModel.createJob(
            title='Climos: ' + inFolder['name'], type='climos',
            handler='romanesco_handler', user=user)
        token = self.model('token').createToken(user=user, days=3)

        task = {
            'mode': 'python',
            'script': _climos_script,
            'inputs': [{
                'id': 'in_dir',
                'type': 'string',
                'format': 'text'
            }, {
                'id': 'out_filename',
                'type': 'string',
                'format': 'text'
            }, {
                'id': 'variables',
                'type': 'python',
                'format': 'object'
            }, {
                'id': 'seasons',
                'type': 'python',
                'format': 'object'
            }],
            'outputs': [{
                'id': 'outfile',
                'type': 'string',
                'format': 'text'
            }]
        }

        girderIoParams = {
            'mode': 'girder',
            'host': urlParts.hostname,
            'port': urlParts.port,
            'api_root': rest.getApiUrl(urlParts.path),
            'scheme': urlParts.scheme,
            'token': token['_id']
        }

        inputs = {
            'in_dir': dict(girderIoParams, **{
                'method': 'GET',
                'id': str(inFolder['_id']),
                'resource_type': 'folder',
                'type': 'string',
                'format': 'text',
                'name': inFolder['name']
            }),
            'seasons': {
                'mode': 'inline',
                'type': 'python',
                'format': 'object',
                'data': json.loads(params['seasons'])
            },
            'variables': {
                'mode': 'inline',
                'type': 'python',
                'format': 'object',
                'data': json.loads(params['vars'])
            },
            'out_filename': {
                'mode': 'inline',
                'type': 'string',
                'format': 'text',
                'data': params['outputFilename'].strip()
            }
        }

        outputs = {
            'outfile': dict(girderIoParams, **{
                'parent_type': 'folder',
                'parent_id': str(outFolder['_id']),
                'format': 'text',
                'type': 'string'
            })
        }

        job['kwargs'] = {
            'task': task,
            'inputs': inputs,
            'outputs': outputs,
            'jobInfo': {
                'method': 'PUT',
                'url': '/'.join((apiUrl, 'job', str(job['_id']))),
                'headers': {'Girder-Token': token['_id']},
                'logPrint': True
            },
            'validate': False,
            'auto_convert': True,
            'cleanup': True
        }
        job = jobModel.save(job)
        jobModel.scheduleJob(job)

        return jobModel.filter(job, user)
    runClimos.description = (
        Description('Run the climos task in romanesco.')
        .param('inputFolderId', 'The folder containing input files.')
        .param('outputFolderId', 'The folder to upload the output into.')
        .param('vars', 'JSON list of vars to use.')
        .param('seasons', 'JSON list of season identifiers.')
        .param('outputFilename', 'The name of the output file.'))


def load(info):
    info['apiRoot'].climos = Climos()
