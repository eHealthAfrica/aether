# NEW_STR = '''
#         SELECT
#             e.id,
#             e.modified
#         FROM kernel_entity e
#         inner join kernel_projectschema ps on e.projectschema_id = ps.id
#         inner join kernel_schema s on ps.schema_id = s.id
#         WHERE e.modified > {modified}
#         AND s.name = {schema_name}
#         LIMIT 1; '''

#     # Count how many unique (controlled by kernel) messages should currently be in this topic
#     COUNT_STR = '''
#             SELECT
#                 count(e.id)
#             FROM kernel_entity e
#             inner join kernel_projectschema ps on e.projectschema_id = ps.id
#             inner join kernel_schema s on ps.schema_id = s.id
#             WHERE s.name = {schema_name};
#     '''

#     # Changes pull query
#     QUERY_STR = '''
#             SELECT
#                 e.id,
#                 e.revision,
#                 e.payload,
#                 e.modified,
#                 e.status,
#                 ps.id as project_schema_id,
#                 ps.name as project_schema_name,
#                 s.name as schema_name,
#                 s.id as schema_id,
#                 s.revision as schema_revision
#             FROM kernel_entity e
#             inner join kernel_projectschema ps on e.projectschema_id = ps.id
#             inner join kernel_schema s on ps.schema_id = s.id
#             WHERE e.modified > {modified}
#             AND s.name = {schema_name}
#             ORDER BY e.modified ASC
#             LIMIT {limit};
#         '''

# are there any new entities, regardless of tenant, etc
NEW_STR = '''
        SELECT
            e.id,
            e.modified
        FROM kernel_entity e
        inner join kernel_projectschema ps on e.projectschema_id = ps.id
        inner join kernel_schema s on ps.schema_id = s.id
        WHERE e.modified > {modified}
        LIMIT 1; '''

# get matching project schemas between start and some end time

# Changes pull query
QUERY_STR = '''
        SELECT
            e.id,
            e.revision,
            e.payload,
            e.modified,
            e.status,
            ps.id as project_schema_id,
            ps.name as project_schema_name,
            s.name as schema_name,
            s.id as schema_id,
            s.revision as schema_revision,
            MT.realm as realm
        FROM kernel_entity e
        inner join kernel_projectschema ps on e.projectschema_id = ps.id
        inner join kernel_schema s on ps.schema_id = s.id
        inner join multitenancy_mtinstance MT on e.project_id = MT.instance_id
        WHERE e.modified > {start_modified}
        AND e.modified <= {end_modified}
        AND ps.id in ({project_schema_ids})  # should be formatted (1, 2, 3)
        ORDER BY e.modified ASC
        LIMIT {limit};  # probably don't need a limit if we're just throwing into Redis
    '''

# Count how many unique (controlled by kernel) messages should currently be in this topic
COUNT_STR = '''
        SELECT
            count(e.id)
        FROM kernel_entity e
        inner join kernel_projectschema ps on e.projectschema_id = ps.id
        inner join kernel_schema s on ps.schema_id = s.id
        WHERE ps.id in ({project_schema_ids}); # should be formatted (1, 2, 3)
'''


# SELECT MT.realm, E.*
# FROM multitenancy_mtinstance MT
# INNER JOIN kernel_project P
#   ON MT.instance_id = P.id
# INNER JOIN kernel_entity E
#   ON E.project_id = P.id