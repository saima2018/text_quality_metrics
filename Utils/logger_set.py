import yaml
import logging.config
import os
import sys
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)

# 使用方法，主文件里面写入这两行logger = logging.getLogger(__file__)，setup_log = setup_logging()；
# 其他文件里面import logging, 写入logger = logging.getLogger(__file__)

logger = logging.getLogger(__file__)


def setup_logging(base_dir=None,default_path=os.path.join(root_path,"conf/logger.yaml"), default_level=logging.INFO, env_key="LOG_CFG"):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    print('base_dir=====================\n',base_dir)
    log_dir = os.path.join(base_dir, 'logs')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
        print(path)
    if os.path.exists(path):
        with open(path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
    return True


def func():
    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")


setup_log = setup_logging()

if __name__ == "__main__":
    func()
