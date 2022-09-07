import logging

# Здесь задана глобальная конфигурация для всех логгеров
logging.basicConfig(
    level=logging.INFO,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

# А тут установлены настройки логгера
logger = logging.getLogger(__name__)
# Устанавливаем уровень, с которого логи будут сохраняться в файл
logger.setLevel(logging.INFO)

logger.info('Сообщение отправлено')
logger.warning('Большая нагрузка!')
logger.error('Cбой при отправке сообщения в Telegram ')
logger.critical('Всё упало! Зовите админа!1!111')
