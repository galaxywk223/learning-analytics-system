--
-- PostgreSQL database dump
--

\restrict b3VKJkdrNavvCFNsfcdmA95IPEVpXkXdDPTHY4KmRBxBxNPn0Ea9WDaqlDaLQGj

-- Dumped from database version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_insight; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.ai_insight (
    id integer NOT NULL,
    user_id integer NOT NULL,
    insight_type character varying(20) NOT NULL,
    scope character varying(20) NOT NULL,
    scope_reference integer,
    start_date date,
    end_date date,
    next_start_date date,
    next_end_date date,
    input_snapshot json,
    output_text text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.ai_insight OWNER TO kai;

--
-- Name: ai_insight_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.ai_insight_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ai_insight_id_seq OWNER TO kai;

--
-- Name: ai_insight_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.ai_insight_id_seq OWNED BY public.ai_insight.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO kai;

--
-- Name: category; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.category (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.category OWNER TO kai;

--
-- Name: category_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.category_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.category_id_seq OWNER TO kai;

--
-- Name: category_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.category_id_seq OWNED BY public.category.id;


--
-- Name: countdown_event; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.countdown_event (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    target_datetime_utc timestamp with time zone NOT NULL,
    created_at_utc timestamp with time zone,
    user_id integer NOT NULL
);


ALTER TABLE public.countdown_event OWNER TO kai;

--
-- Name: countdown_event_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.countdown_event_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.countdown_event_id_seq OWNER TO kai;

--
-- Name: countdown_event_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.countdown_event_id_seq OWNED BY public.countdown_event.id;


--
-- Name: daily_data; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.daily_data (
    id integer NOT NULL,
    log_date date NOT NULL,
    efficiency double precision,
    stage_id integer NOT NULL
);


ALTER TABLE public.daily_data OWNER TO kai;

--
-- Name: daily_data_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.daily_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.daily_data_id_seq OWNER TO kai;

--
-- Name: daily_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.daily_data_id_seq OWNED BY public.daily_data.id;


--
-- Name: daily_plan_item; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.daily_plan_item (
    id integer NOT NULL,
    plan_date date NOT NULL,
    content character varying(500) NOT NULL,
    time_slot character varying(20),
    is_completed boolean NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.daily_plan_item OWNER TO kai;

--
-- Name: daily_plan_item_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.daily_plan_item_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.daily_plan_item_id_seq OWNER TO kai;

--
-- Name: daily_plan_item_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.daily_plan_item_id_seq OWNED BY public.daily_plan_item.id;


--
-- Name: log_entry; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.log_entry (
    id integer NOT NULL,
    log_date date NOT NULL,
    time_slot character varying(50),
    task character varying(200) NOT NULL,
    actual_duration integer,
    legacy_category character varying(100),
    mood integer,
    notes text,
    stage_id integer NOT NULL,
    subcategory_id integer,
    created_at timestamp without time zone
);


ALTER TABLE public.log_entry OWNER TO kai;

--
-- Name: log_entry_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.log_entry_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.log_entry_id_seq OWNER TO kai;

--
-- Name: log_entry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.log_entry_id_seq OWNED BY public.log_entry.id;


--
-- Name: milestone; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.milestone (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    event_date date NOT NULL,
    description text,
    user_id integer NOT NULL,
    category_id integer,
    created_at timestamp without time zone
);


ALTER TABLE public.milestone OWNER TO kai;

--
-- Name: milestone_attachment; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.milestone_attachment (
    id integer NOT NULL,
    milestone_id integer NOT NULL,
    file_path character varying(256) NOT NULL,
    original_filename character varying(200) NOT NULL,
    uploaded_at timestamp without time zone
);


ALTER TABLE public.milestone_attachment OWNER TO kai;

--
-- Name: milestone_attachment_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.milestone_attachment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.milestone_attachment_id_seq OWNER TO kai;

--
-- Name: milestone_attachment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.milestone_attachment_id_seq OWNED BY public.milestone_attachment.id;


--
-- Name: milestone_category; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.milestone_category (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.milestone_category OWNER TO kai;

--
-- Name: milestone_category_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.milestone_category_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.milestone_category_id_seq OWNER TO kai;

--
-- Name: milestone_category_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.milestone_category_id_seq OWNED BY public.milestone_category.id;


--
-- Name: milestone_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.milestone_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.milestone_id_seq OWNER TO kai;

--
-- Name: milestone_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.milestone_id_seq OWNED BY public.milestone.id;


--
-- Name: motto; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.motto (
    id integer NOT NULL,
    content text NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.motto OWNER TO kai;

--
-- Name: motto_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.motto_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.motto_id_seq OWNER TO kai;

--
-- Name: motto_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.motto_id_seq OWNED BY public.motto.id;


--
-- Name: setting; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.setting (
    key character varying(50) NOT NULL,
    value character varying(200) NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.setting OWNER TO kai;

--
-- Name: stage; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.stage (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    start_date date NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.stage OWNER TO kai;

--
-- Name: stage_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.stage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.stage_id_seq OWNER TO kai;

--
-- Name: stage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.stage_id_seq OWNED BY public.stage.id;


--
-- Name: sub_category; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.sub_category (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    category_id integer NOT NULL
);


ALTER TABLE public.sub_category OWNER TO kai;

--
-- Name: sub_category_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.sub_category_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sub_category_id_seq OWNER TO kai;

--
-- Name: sub_category_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.sub_category_id_seq OWNED BY public.sub_category.id;


--
-- Name: todo; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.todo (
    id integer NOT NULL,
    content text NOT NULL,
    due_date date,
    priority integer,
    is_completed boolean NOT NULL,
    created_at timestamp without time zone,
    completed_at timestamp without time zone,
    user_id integer NOT NULL
);


ALTER TABLE public.todo OWNER TO kai;

--
-- Name: todo_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.todo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.todo_id_seq OWNER TO kai;

--
-- Name: todo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.todo_id_seq OWNED BY public.todo.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    username character varying(64) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(256),
    created_at timestamp without time zone
);


ALTER TABLE public."user" OWNER TO kai;

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_id_seq OWNER TO kai;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: weekly_data; Type: TABLE; Schema: public; Owner: kai
--

CREATE TABLE public.weekly_data (
    id integer NOT NULL,
    year integer NOT NULL,
    week_num integer NOT NULL,
    efficiency double precision,
    stage_id integer NOT NULL
);


ALTER TABLE public.weekly_data OWNER TO kai;

--
-- Name: weekly_data_id_seq; Type: SEQUENCE; Schema: public; Owner: kai
--

CREATE SEQUENCE public.weekly_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.weekly_data_id_seq OWNER TO kai;

--
-- Name: weekly_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kai
--

ALTER SEQUENCE public.weekly_data_id_seq OWNED BY public.weekly_data.id;


--
-- Name: ai_insight id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.ai_insight ALTER COLUMN id SET DEFAULT nextval('public.ai_insight_id_seq'::regclass);


--
-- Name: category id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.category ALTER COLUMN id SET DEFAULT nextval('public.category_id_seq'::regclass);


--
-- Name: countdown_event id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.countdown_event ALTER COLUMN id SET DEFAULT nextval('public.countdown_event_id_seq'::regclass);


--
-- Name: daily_data id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.daily_data ALTER COLUMN id SET DEFAULT nextval('public.daily_data_id_seq'::regclass);


--
-- Name: daily_plan_item id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.daily_plan_item ALTER COLUMN id SET DEFAULT nextval('public.daily_plan_item_id_seq'::regclass);


--
-- Name: log_entry id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.log_entry ALTER COLUMN id SET DEFAULT nextval('public.log_entry_id_seq'::regclass);


--
-- Name: milestone id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.milestone ALTER COLUMN id SET DEFAULT nextval('public.milestone_id_seq'::regclass);


--
-- Name: milestone_attachment id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.milestone_attachment ALTER COLUMN id SET DEFAULT nextval('public.milestone_attachment_id_seq'::regclass);


--
-- Name: milestone_category id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.milestone_category ALTER COLUMN id SET DEFAULT nextval('public.milestone_category_id_seq'::regclass);


--
-- Name: motto id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.motto ALTER COLUMN id SET DEFAULT nextval('public.motto_id_seq'::regclass);


--
-- Name: stage id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.stage ALTER COLUMN id SET DEFAULT nextval('public.stage_id_seq'::regclass);


--
-- Name: sub_category id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.sub_category ALTER COLUMN id SET DEFAULT nextval('public.sub_category_id_seq'::regclass);


--
-- Name: todo id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.todo ALTER COLUMN id SET DEFAULT nextval('public.todo_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: weekly_data id; Type: DEFAULT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.weekly_data ALTER COLUMN id SET DEFAULT nextval('public.weekly_data_id_seq'::regclass);


--
-- Name: daily_data _stage_log_date_uc; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.daily_data
    ADD CONSTRAINT _stage_log_date_uc UNIQUE (log_date, stage_id);


--
-- Name: weekly_data _stage_year_week_uc; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.weekly_data
    ADD CONSTRAINT _stage_year_week_uc UNIQUE (year, week_num, stage_id);


--
-- Name: ai_insight ai_insight_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.ai_insight
    ADD CONSTRAINT ai_insight_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: category category_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.category
    ADD CONSTRAINT category_pkey PRIMARY KEY (id);


--
-- Name: countdown_event countdown_event_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.countdown_event
    ADD CONSTRAINT countdown_event_pkey PRIMARY KEY (id);


--
-- Name: daily_data daily_data_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.daily_data
    ADD CONSTRAINT daily_data_pkey PRIMARY KEY (id);


--
-- Name: daily_plan_item daily_plan_item_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.daily_plan_item
    ADD CONSTRAINT daily_plan_item_pkey PRIMARY KEY (id);


--
-- Name: log_entry log_entry_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.log_entry
    ADD CONSTRAINT log_entry_pkey PRIMARY KEY (id);


--
-- Name: milestone_attachment milestone_attachment_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.milestone_attachment
    ADD CONSTRAINT milestone_attachment_pkey PRIMARY KEY (id);


--
-- Name: milestone_category milestone_category_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.milestone_category
    ADD CONSTRAINT milestone_category_pkey PRIMARY KEY (id);


--
-- Name: milestone milestone_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.milestone
    ADD CONSTRAINT milestone_pkey PRIMARY KEY (id);


--
-- Name: motto motto_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.motto
    ADD CONSTRAINT motto_pkey PRIMARY KEY (id);


--
-- Name: setting setting_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.setting
    ADD CONSTRAINT setting_pkey PRIMARY KEY (key, user_id);


--
-- Name: stage stage_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.stage
    ADD CONSTRAINT stage_pkey PRIMARY KEY (id);


--
-- Name: sub_category sub_category_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.sub_category
    ADD CONSTRAINT sub_category_pkey PRIMARY KEY (id);


--
-- Name: todo todo_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.todo
    ADD CONSTRAINT todo_pkey PRIMARY KEY (id);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: weekly_data weekly_data_pkey; Type: CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.weekly_data
    ADD CONSTRAINT weekly_data_pkey PRIMARY KEY (id);


--
-- Name: ix_ai_insight_user_id; Type: INDEX; Schema: public; Owner: kai
--

CREATE INDEX ix_ai_insight_user_id ON public.ai_insight USING btree (user_id);


--
-- Name: ix_daily_data_log_date; Type: INDEX; Schema: public; Owner: kai
--

CREATE INDEX ix_daily_data_log_date ON public.daily_data USING btree (log_date);


--
-- Name: ix_daily_plan_item_plan_date; Type: INDEX; Schema: public; Owner: kai
--

CREATE INDEX ix_daily_plan_item_plan_date ON public.daily_plan_item USING btree (plan_date);


--
-- Name: ix_log_entry_log_date; Type: INDEX; Schema: public; Owner: kai
--

CREATE INDEX ix_log_entry_log_date ON public.log_entry USING btree (log_date);


--
-- Name: ix_milestone_event_date; Type: INDEX; Schema: public; Owner: kai
--

CREATE INDEX ix_milestone_event_date ON public.milestone USING btree (event_date);


--
-- Name: ix_user_email; Type: INDEX; Schema: public; Owner: kai
--

CREATE UNIQUE INDEX ix_user_email ON public."user" USING btree (email);


--
-- Name: ix_user_username; Type: INDEX; Schema: public; Owner: kai
--

CREATE UNIQUE INDEX ix_user_username ON public."user" USING btree (username);


--
-- Name: category category_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.category
    ADD CONSTRAINT category_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: countdown_event countdown_event_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.countdown_event
    ADD CONSTRAINT countdown_event_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: daily_data daily_data_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.daily_data
    ADD CONSTRAINT daily_data_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.stage(id);


--
-- Name: daily_plan_item daily_plan_item_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.daily_plan_item
    ADD CONSTRAINT daily_plan_item_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: ai_insight fk_ai_insight_user_id; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.ai_insight
    ADD CONSTRAINT fk_ai_insight_user_id FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: log_entry log_entry_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.log_entry
    ADD CONSTRAINT log_entry_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.stage(id);


--
-- Name: log_entry log_entry_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.log_entry
    ADD CONSTRAINT log_entry_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.sub_category(id);


--
-- Name: milestone_attachment milestone_attachment_milestone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.milestone_attachment
    ADD CONSTRAINT milestone_attachment_milestone_id_fkey FOREIGN KEY (milestone_id) REFERENCES public.milestone(id);


--
-- Name: milestone milestone_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.milestone
    ADD CONSTRAINT milestone_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.milestone_category(id);


--
-- Name: milestone_category milestone_category_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.milestone_category
    ADD CONSTRAINT milestone_category_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: milestone milestone_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.milestone
    ADD CONSTRAINT milestone_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: motto motto_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.motto
    ADD CONSTRAINT motto_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: setting setting_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.setting
    ADD CONSTRAINT setting_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: stage stage_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.stage
    ADD CONSTRAINT stage_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: sub_category sub_category_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.sub_category
    ADD CONSTRAINT sub_category_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.category(id);


--
-- Name: todo todo_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.todo
    ADD CONSTRAINT todo_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: weekly_data weekly_data_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: kai
--

ALTER TABLE ONLY public.weekly_data
    ADD CONSTRAINT weekly_data_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.stage(id);


--
-- PostgreSQL database dump complete
--

\unrestrict b3VKJkdrNavvCFNsfcdmA95IPEVpXkXdDPTHY4KmRBxBxNPn0Ea9WDaqlDaLQGj

