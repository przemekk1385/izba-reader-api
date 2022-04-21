from enum import Enum


class UploadImagesError(Enum):
    INVALID_ASPECT_RATIO = "INVALID_ASPECT_RATIO"
    UNHANDLED_MIME_TYPE = "UNHANDLED_MIME_TYPE"
