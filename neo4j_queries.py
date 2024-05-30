"""
Widget 3 Queries
"""


# Function: Display a table of top collaborators based on number of shared publications
pub_collab_cts_query = "MATCH (f1:FACULTY)-[:PUBLISH]->(publication:PUBLICATION)<-[:PUBLISH]-(f2:FACULTY) \
                        WHERE f1 <> f2 AND f1.name < f2.name \
                        RETURN f1.name AS faculty1, f2.name AS faculty2, COUNT(publication) AS collaboration_count \
                        ORDER BY collaboration_count DESC \
                        LIMIT 100"
