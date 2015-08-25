from girder.api.rest import Resource, loadmodel
from girder.api.describe import Description
from girder.constants import AccessType


class Climos(Resource):
    def __init__(self):
        self.route('POST', (), 'runClimos')

    @loadmodel(map={'folderId': 'folder'}, model='folder',
               level=AccessType.READ)
    def runClimos(self, folder, params):
        self.requireParams(('seasons', 'vars') params)
        # TODO create task

    runClimos.description = (
        Description('Run the climos task in romanesco.')
        .param('folderId', 'The folder containing input files.')
        .param('vars', 'JSON list of vars to use.')
        .param('seasons', 'JSON list of season identifiers.'))


def load(info):
    info['apiRoot'].climos = Climos()
