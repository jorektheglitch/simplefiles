from simplefiles.core.entities import Media
from simplefiles.services import FilesService

from .utils import APIRequest, Response
from .utils.response import Status


class StoreFile(APIRequest):
    pass


async def store_file(files_service: FilesService, request: StoreFile) -> Response[Media]:
    async with files_service.tempfile() as tmp:
        media = await files_service.materialize(tmp)
    return Response(media, Status.CREATED)
