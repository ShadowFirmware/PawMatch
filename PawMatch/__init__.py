# Configurar PyMySQL como driver de MySQL para Django
import pymysql

# PyMySQL se comporta como mysqlclient
pymysql.install_as_MySQLdb()
