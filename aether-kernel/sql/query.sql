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

REVOKE ALL PRIVILEGES ON DATABASE {database} FROM {role_id} CASCADE;
GRANT  CONNECT        ON DATABASE {database} TO   {role_id};
GRANT  USAGE          ON SCHEMA public       TO   {role_id};
GRANT  SELECT         ON kernel_schema_vw    TO   {role_id};
GRANT  SELECT         ON kernel_entity_vw    TO   {role_id};
