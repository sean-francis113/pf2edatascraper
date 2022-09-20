#Import Statements
import pymysql.cursors
import pymysql.err
import user_data.user_data

from lib.log import log_text as log

def connect_to_database():
  """
	Function That Connects to the Database
	"""
  log("Connecting to " + user_data.user_data.db_database)
  #Connect to Database With Environment Values
  conn = pymysql.connect(
    host=user_data.user_data.db_host,
    user=user_data.user_data.db_user,
    passwd=user_data.user_data.db_password,
    db=user_data.user_data.db_database,
    charset="utf8mb4")

  if conn is not None:
      log("Connection Successful")
  else:
      log("Connection Failure")
  #Return the Connection
  return conn


def query_database(query,
                  connection=None,
                  commit=False,
                  get_result=False,
                  close_conn=True):
    """
	Execute a Query into Database, Connecting if Necessary, and Return the Result if Desired

	Parameters:
	-----------
		query (string)
			String of the MySQL Query
		connection (pymysql.connections.Connection, OPTIONAL)
			The Connection to the Database. If Not Provided, a Connection Will Be Made Before Making the Query
		commit (boolean, OPTIONAL)
			If We Should Commit the Query to the Database
		get_result (boolean, OPTIONAL)
			If We Should Get the Results of the Query
		close_conn (boolean, OPTIONAL)
			If We Should Close the Connection Once We Are Done With the Query
	"""

    result = None
    rowCount = 0

    if connection == None:
      connection = connect_to_database()

    log("Executing Query: " + query)
    cur = connection.cursor()
    row_count = cur.execute(query)

    if get_result == True and row_count > 0:
      log("Grabbing Result of Query")
      result = cur.fetchall()

    if commit == True:
      log("Commiting Database Changes")
      connection.commit()

    log("Closing Cursor")
    cur.close()

    if close_conn == True:
      log("Closing Connection")
      connection.close()

    return connection, row_count, result
