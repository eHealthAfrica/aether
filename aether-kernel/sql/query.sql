DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = {role_literal})
  THEN
    CREATE ROLE {role_id}
      WITH LOGIN ENCRYPTED
      PASSWORD {password}
      INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
  END IF;
END
$$ LANGUAGE plpgsql;


DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'multitenancy_mtinstance')
  THEN
    DROP VIEW IF EXISTS multitenancy_mtinstance CASCADE;
    CREATE VIEW multitenancy_mtinstance AS
      SELECT '-'  AS realm,
             p.id AS instance_id
      FROM kernel_project;
  END IF;
END
$$ LANGUAGE plpgsql;


DROP VIEW IF EXISTS kernel_entity_vw CASCADE;
DROP VIEW IF EXISTS kernel_schema_vw CASCADE;

CREATE VIEW kernel_schema_vw AS
  SELECT
    GREATEST(sd.modified, s.modified) AS modified,

    sd.id                             AS schemadecorator_id,
    sd.name                           AS schemadecorator_name,

    s.id                              AS schema_id,
    s.name                            AS schema_name,
    s.definition                      AS schema_definition,
    s.revision                        AS schema_revision,

    mt.realm                          AS realm,

    (s.family = sd.project_id::text)  AS is_identity

  FROM kernel_schemadecorator         AS sd
  INNER JOIN kernel_schema            AS s
          ON sd.schema_id = s.id
  INNER JOIN multitenancy_mtinstance  AS mt
          ON sd.project_id = mt.instance_id
  ORDER BY 1 ASC
  ;

CREATE VIEW kernel_entity_vw AS
  SELECT
      e.id,
      e.revision,
      e.payload,
      e.modified,
      e.status,

      s.schemadecorator_id,
      s.schemadecorator_name,
      s.schema_name,
      s.schema_id,
      s.schema_revision,
      s.realm

  FROM kernel_entity          AS e
  INNER JOIN kernel_schema_vw AS s
          ON e.schemadecorator_id = s.schemadecorator_id
  ORDER BY e.modified ASC
  ;


REVOKE ALL PRIVILEGES ON DATABASE {database} FROM {role_id} CASCADE;
GRANT CONNECT         ON DATABASE {database} TO   {role_id};

GRANT USAGE ON SCHEMA public            TO {role_id};

GRANT SELECT ON kernel_entity           TO {role_id};
GRANT SELECT ON kernel_mapping          TO {role_id};
GRANT SELECT ON kernel_schemadecorator  TO {role_id};
GRANT SELECT ON kernel_schema           TO {role_id};
GRANT SELECT ON kernel_project          TO {role_id};
GRANT SELECT ON multitenancy_mtinstance TO {role_id};

GRANT SELECT ON kernel_schema_vw        TO {role_id};
GRANT SELECT ON kernel_entity_vw        TO {role_id};
