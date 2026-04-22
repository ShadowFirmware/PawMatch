# Configurar PyMySQL como driver de MySQL para Django
import pymysql

# PyMySQL se comporta como mysqlclient
pymysql.install_as_MySQLdb()

# Fix para Django que verifica la versión de mysqlclient
import MySQLdb
MySQLdb.version_info = (2, 2, 1, 'final', 0)
MySQLdb.__version__ = '2.2.1'
