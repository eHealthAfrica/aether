DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readonlyuser')
  THEN
      CREATE ROLE readonlyuser WITH LOGIN ENCRYPTED PASSWORD ':password'
      INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
  END IF;
END
$$ LANGUAGE plpgsql;

\connect aether
GRANT CONNECT ON DATABASE aether TO readonlyuser;
GRANT USAGE ON SCHEMA public TO readonlyuser;
GRANT SELECT ON kernel_entity TO readonlyuser;
GRANT SELECT ON kernel_mapping TO readonlyuser;
GRANT SELECT ON kernel_projectschema TO readonlyuser;
GRANT SELECT ON kernel_schema TO readonlyuser;
