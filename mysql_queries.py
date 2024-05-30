"""
Widget 1 Queries
"""

w1_stored_procedure = "CREATE PROCEDURE GetKeywordCitations(IN kwd VARCHAR(255), IN year_start INT, IN year_end INT) " \
                        "BEGIN \
                         SELECT publication.year, COUNT(*) as keyword_count \
                         FROM keyword \
                         INNER JOIN publication_keyword ON keyword.id=publication_keyword.keyword_id \
                         INNER JOIN publication ON publication.id=publication_keyword.publication_id \
                         WHERE (keyword.name = kwd) " \
                            "AND (publication.year >= year_start) " \
                            "AND (publication.year <= year_end) \
                         GROUP BY publication.year \
                         ORDER BY publication.year ASC; \
                         END;"

"""
Widget 4 Queries
"""

publication_keyword_names_query = "SELECT DISTINCT keyword.name as keyword_names \
                                  FROM keyword \
                                  INNER JOIN publication_keyword ON keyword.id=publication_keyword.keyword_id \
                                  INNER JOIN publication ON publication.id=publication_keyword.publication_id \
                                  ORDER BY keyword.name ASC;"

w4_stored_procedure = "CREATE PROCEDURE GetFacultyPairKeywords(IN faculty_name_1 VARCHAR(255), " \
                                                                "IN faculty_name_2 VARCHAR(255)) BEGIN \
                        SELECT \
                            t1.faculty_id, \
                            f1.name, \
                            t2.faculty_id, \
                            f2.name, \
                            GROUP_CONCAT(DISTINCT keyword.name ORDER BY keyword.name SEPARATOR ', ') " \
                                "AS shared_keyword_names, \
                            COUNT(DISTINCT t1.keyword_id) AS shared_keywords_count \
                        FROM \
                            faculty_keyword t1 \
                        INNER JOIN \
                            faculty_keyword t2 ON t1.keyword_id = t2.keyword_id \
                        INNER JOIN \
                            keyword ON t1.keyword_id = keyword.id \
                        INNER JOIN \
                            faculty as f1 ON t1.faculty_id = f1.id \
                        INNER JOIN \
                            faculty as f2 ON t2.faculty_id = f2.id \
                        WHERE \
                            f1.id > f2.id \
                            AND \
                            (f1.name=faculty_name_1 OR f2.name=faculty_name_1) \
                            AND \
                            (f1.name=faculty_name_2 or f2.name=faculty_name_2) \
                        GROUP BY \
                            t1.faculty_id, t2.faculty_id \
                        LIMIT 1; \
                        END;"

w4_faculty_keyword_insertion_transaction_query = "BEGIN; \
    INSERT INTO faculty_keyword (faculty_id, keyword_id, score) VALUES ({}, {}, 0); \
    INSERT INTO faculty_keyword (faculty_id, keyword_id, score) VALUES ({}, {}, 0); \
    COMMIT;"

w4_faculty_keyword_insertion_transaction_query_list = [
    "BEGIN;",
    "INSERT IGNORE INTO faculty_keyword (faculty_id, keyword_id, score) VALUES ({}, {}, 0);",
    "INSERT IGNORE INTO faculty_keyword (faculty_id, keyword_id, score) VALUES ({}, {}, 0);",
    "COMMIT;"]

"""
Widget 5 Queries
"""
w5_view_creation_query = "CREATE VIEW faculty_publication_view AS \
                 SELECT faculty.id as faculty_id, faculty.name as faculty_name, publication.id as publication_id, " \
                         "publication.num_citations, university.name as university_name \
                 FROM faculty \
                 JOIN faculty_publication on faculty.id = faculty_publication.faculty_id \
                 JOIN publication on publication.id = faculty_publication.publication_id \
                 JOIN university on university.id = faculty.university_id \
                 WHERE university.name = '{}';"

w5_h_index_creation_query = "SELECT faculty_name, MAX(h_index) AS h_index \
                FROM ( \
                SELECT faculty_name, \
                CASE WHEN ROW_NUMBER() OVER (PARTITION BY faculty_name ORDER BY num_citations DESC) <= num_citations " \
                    "THEN ROW_NUMBER() OVER (PARTITION BY faculty_name ORDER BY num_citations DESC) " \
                    "ELSE 0 END AS h_index \
                FROM faculty_publication_view \
                ) AS subquery \
                GROUP BY faculty_name \
                ORDER BY h_index DESC;"

"""
Widget 6 Queries
"""

w6_query = "SELECT faculty.id as faculty_id, faculty.name as faculty_name, university.name as university_name \
                                                    FROM faculty \
                                                    JOIN university on university.id = faculty.university_id \
                                                    WHERE faculty.name IN ("