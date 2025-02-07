import loglady

logger = loglady.bind()
loglady.log("loglady.log() before calling configure")
logger.log("logger.log() before calling configure")

loglady.configure()

loglady.log("loglady.log() after calling configure")
logger.log("logger.log() after calling configure")
