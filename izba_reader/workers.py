from uvicorn import workers

from izba_reader.constants import BASE_DIR


class UvicornWorker(workers.UvicornWorker):
    CONFIG_KWARGS = {
        "log_config": str(BASE_DIR / "logging.yaml"),
    }
