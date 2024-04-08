/* === Define Types === */

/* Uregency Type */
DO $$ BEGIN
    CREATE TYPE urgency AS ENUM ('High', 'Medium', 'Low');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

/* Impact Type */
DO $$ BEGIN
    CREATE TYPE impact AS ENUM ('High', 'Medium', 'Low');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

/* Incident Status Type */
DO $$ BEGIN
    CREATE TYPE incident_status AS ENUM ('Open', 'In Progress', 'User Action', 'Closed');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

/* uuid-ossp — a UUID generator */
DO $$ BEGIN
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


/* === Define Tables === */

/* Users Table */
CREATE TABLE
    IF NOT EXISTS public.t_user (
        id UUID DEFAULT uuid_generate_v4 () PRIMARY KEY NOT NULL,
        username VARCHAR(50) UNIQUE NOT NULL,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
        telegram_user_id BIGINT
    );

/* Incidents Table */
CREATE TABLE
    IF NOT EXISTS public.t_incident (
        id UUID DEFAULT uuid_generate_v4 () PRIMARY KEY NOT NULL,
        reported_by UUID DEFAULT uuid_generate_v4 (),
        reported_at DEFAULT NOW() TIMESTAMPTZ NOT NULL,
        description TEXT,
        urgency urgency NOT NULL,
        impact impact NOT NULL,
        CONSTRAINT fk_t_user
            FOREIGN KEY (reported_by)
                REFERENCES public.t_user (id)
                    ON DELETE CASCADE
    );

/* Comments Table */
CREATE TABLE
    IF NOT EXISTS public.t_comment (
        created_by UUID DEFAULT uuid_generate_v4 () NOT NULL,
        incident_id UUID DEFAULT uuid_generate_v4 () NOT NULL,
        created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
        incident_status incident_status NOT NULL,
        comment TEXT,
        CONSTRAINT fk_t_user
            FOREIGN KEY (created_by)
                REFERENCES public.t_user (id)
                    ON DELETE CASCADE,
        CONSTRAINT fk_t_incident
            FOREIGN KEY (incident_id)
                REFERENCES public.t_incident (id)
                    ON DELETE CASCADE
    );

/* Tags Table */
CREATE TABLE
    IF NOT EXISTS public.t_tag (
        id UUID DEFAULT uuid_generate_v4 () PRIMARY KEY,
        name VARCHAR(20) UNIQUE NOT NULL
    );

/* Incident tags Table */
CREATE TABLE
    IF NOT EXISTS public.t_incident_tag (
        incident_id UUID DEFAULT uuid_generate_v4 (),
        tag_id UUID DEFAULT uuid_generate_v4 (),
        CONSTRAINT fk_t_incident
            FOREIGN KEY (incident_id)
                REFERENCES public.t_incident (id)
                    ON DELETE CASCADE,
        CONSTRAINT fk_t_tag
            FOREIGN KEY (tag_id)
                REFERENCES public.t_tag
                    ON DELETE CASCADE
    );


/* === Define View === */
CREATE OR REPLACE VIEW public.v_incident AS
    SELECT
    t_incident.id AS incident_id,
    t_reporter.username AS reported_by_username, 
    t_processor.username AS processed_by_username,
    t_incident.reported_at AS reported_at,
    t_comment.created_at AS updated_at,
    t_comment.incident_status AS incident_status,
    t_incident.description AS description,
    t_incident.urgency AS urgency,
    t_incident.impact AS impact,
    t_tags.tags AS tags
    FROM public.t_incident
    LEFT JOIN public.t_user AS t_reporter ON t_incident.reported_by = t_reporter.id
    LEFT JOIN (
        SELECT created_at, created_by, incident_status, incident_id
        FROM public.t_comment
        ORDER BY created_at DESC
        LIMIT 1
    ) AS t_comment ON t_comment.incident_id = t_incident.id
    LEFT JOIN public.t_user AS t_processor ON t_comment.created_by = t_processor.id
    LEFT JOIN (
        SELECT incident_id, string_agg(t_tag.name, ', ') as tags
        FROM public.t_incident_tag
        LEFT JOIN public.t_tag ON t_incident_tag.tag_id = t_tag.id
        GROUP BY incident_id
    ) AS t_tags ON t_tags.incident_id = t_incident.id;
