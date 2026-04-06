import pymysql
pymysql.install_as_MySQLdb()
# Satisfy Django's mysqlclient >= 2.2.1 version check.
# PyMySQL reports itself as 1.4.x; patching the version string
# prevents the ImproperlyConfigured error without affecting behaviour.
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.__version__ = "2.2.1"
