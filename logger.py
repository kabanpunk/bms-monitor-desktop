import logging

# Создаем объект логгера
logger = logging.getLogger('app_logger')

# Устанавливаем общий уровень логгирования
logger.setLevel(logging.DEBUG)

# Создаем обработчик, который записывает все DEBUG и выше сообщения в файл
fh = logging.FileHandler('app.log')
fh.setLevel(logging.DEBUG)

# Создаем обработчик, который записывает все ERROR и выше сообщения в консоль
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)


# Создаем форматтер и добавляем его в обработчики
formatter = logging.Formatter('%(asctime)s - [%(filename)s:%(lineno)d] - %(module)s.%(funcName)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# Добавляем обработчики в логгер
logger.addHandler(fh)
logger.addHandler(ch)

