import psycopg2
import mysql.connector

class DatabaseI(object):
    '''Simple database wrapper. This mostly mirrors psycopg2 / mysql.connector 
    functionality with some assurances built in for closing connections 
    upon object destruction.
    
    TODO: check if this is actually required'''
    
    def __init__(self, host, user, database, password="", encoding='latin1'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.encoding = encoding
        self.conn = None
    
    def connect(self):
        raise NotImplementedError()

    def closed(self):
        return False
    
    def cursor(self):
        raise NotImplementedError()        

    def query(self, sql):
        raise NotImplementedError()    
    
    def __enter__(self):
        return self
    
    def __exit__(self, _type, value, traceback):
        pass

    def __del__(self):
        pass


class PostgresSqlConn(DatabaseI):

    def connect(self):
        '''Generate a connection to a PostgreSQL database.
        '''
        conn_string = "host='%s' database='%s'" % (self.host, self.database)
        self.conn = psycopg2.connect(conn_string)
        self.conn.set_client_encoding(self.encoding)
        
    def closed(self):
        return self.conn.closed
        
    def cursor(self): 
        return self.conn.cursor()
    
    def __exit__(self, _type, value, traceback):
        
        if not self.closed():
            self.conn.close()
       
    def __del__(self):
        
        if not self.closed():
            self.conn.close()
            
class MySqlConn(DatabaseI):

    def connect(self):
        '''Generate a connection to a MySQL database.
        '''
        #self.conn.set_client_encoding(self.encoding)
        self.conn = mysql.connector.connect(user=self.user, host=self.host,
                                            password=self.password, 
                                            database=self.database)
        
    def closed(self):
        '''TODO -- don't think this function is correct'''
        #print(self.conn)
        #for x in self.conn.__dict__:
        #    print x
        return self.conn
        
    def cursor(self):
        return self.conn.cursor()
    
    def query(self, sql):
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return [row for row in cursor.fetchall()]
        
    def __exit__(self, _type, value, traceback):  
        if not self.closed():
            print("exiting")
            self.conn.close()
       
    def __del__(self):        
        if not self.closed():
            self.conn.close()
            
