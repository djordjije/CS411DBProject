from neo4j import GraphDatabase

# Define Neo4j connection parameters 
neo4j_URI = "bolt://localhost:7687"
neo4j_AUTH = ("neo4j", "zentarus")

# Test Neo4j driver connection
'''
with GraphDatabase.driver(neo4j_URI, auth=neo4j_AUTH) as driver:
    driver.verify_connectivity()
    records, summary, keys = driver.execute_query("MATCH (f:FACULTY {position: 'Assistant Professor'}) RETURN COUNT(f)",
                                                  database_="academicworld")
    print("Asst. Faculty Ct.: ", records)

'''


# Function to fetch data from the Neo4j localhost
def neo4j_query(query, verify_connectivity=False):
    """
    Attempts to run a Neo4j query and return the records, summary, and keys from the Neo4j driver

    Parameters:
    query (str)        : Text string of the Neo4j query
    verify_connectivity (boolean): Driver parameter to first check connectivity (useful for debugging)

    Returns:
    records, summary, keys variables from the Neo4j driver

    """
    with GraphDatabase.driver(neo4j_URI, auth=neo4j_AUTH) as driver:
        if verify_connectivity:
            driver.verify_connectivity()

        records, summary, keys = driver.execute_query(query, database_="academicworld")
        
        return records, summary, keys
