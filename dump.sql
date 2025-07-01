--
-- PostgreSQL database dump
--

-- Dumped from database version 14.18
-- Dumped by pg_dump version 14.18

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
-- Name: sites; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sites (
    id integer NOT NULL,
    url character varying NOT NULL,
    user_id integer NOT NULL,
    is_available boolean NOT NULL,
    last_checked timestamp with time zone,
    last_notified timestamp with time zone
);


ALTER TABLE public.sites OWNER TO postgres;

--
-- Name: sites_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sites_id_seq OWNER TO postgres;

--
-- Name: sites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sites_id_seq OWNED BY public.sites.id;


--
-- Name: system_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.system_settings (
    id integer NOT NULL,
    key character varying(50) NOT NULL,
    value character varying NOT NULL
);


ALTER TABLE public.system_settings OWNER TO postgres;

--
-- Name: system_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.system_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.system_settings_id_seq OWNER TO postgres;

--
-- Name: system_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.system_settings_id_seq OWNED BY public.system_settings.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    telegram_id bigint NOT NULL,
    username character varying
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: sites id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sites ALTER COLUMN id SET DEFAULT nextval('public.sites_id_seq'::regclass);


--
-- Name: system_settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.system_settings ALTER COLUMN id SET DEFAULT nextval('public.system_settings_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: sites; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.sites VALUES (1, 'https://webjesus.ru', 1, true, '2025-06-30 07:54:05.46391+00', NULL);
INSERT INTO public.sites VALUES (3, 'http://collabapr.com/', 1, true, '2025-06-30 07:54:05.749001+00', NULL);
INSERT INTO public.sites VALUES (44, 'https://vc.ru', 1, true, '2025-06-30 07:54:06.425056+00', NULL);
INSERT INTO public.sites VALUES (4, 'https://dostupsmile.ru/', 4, true, '2025-06-30 07:54:06.721137+00', NULL);
INSERT INTO public.sites VALUES (5, 'https://dostupstom24.ru', 5, true, '2025-06-30 07:54:07.980188+00', NULL);
INSERT INTO public.sites VALUES (7, 'https://dostupsmile.ru/', 5, true, '2025-06-30 07:54:08.092903+00', NULL);
INSERT INTO public.sites VALUES (6, 'https://mpfinassist.io', 6, true, '2025-06-30 07:54:08.395242+00', NULL);
INSERT INTO public.sites VALUES (8, 'https://miradent-58.ru/', 8, true, '2025-06-30 07:54:08.888221+00', NULL);
INSERT INTO public.sites VALUES (41, 'https://dostupstom24.ru', 41, true, '2025-06-30 07:54:09.342892+00', NULL);
INSERT INTO public.sites VALUES (42, 'https://dostupsmile.ru', 41, true, '2025-06-30 07:54:09.410481+00', NULL);
INSERT INTO public.sites VALUES (43, 'https://nsk.stomdostup.ru/', 41, true, '2025-06-30 07:54:10.015531+00', NULL);


--
-- Data for Name: system_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.system_settings VALUES (1, 'check_interval_minutes', '60');


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.users VALUES (1, 11867909, 'webjesus');
INSERT INTO public.users VALUES (2, 1761909893, 'holdonb');
INSERT INTO public.users VALUES (3, 5128947714, 'digitalilia');
INSERT INTO public.users VALUES (4, 701412765, 'RuMarketolog');
INSERT INTO public.users VALUES (5, 415383262, 'userxveronixxx');
INSERT INTO public.users VALUES (6, 144403075, 'sergey_usachev');
INSERT INTO public.users VALUES (7, 1946421717, 'Diam0nd777');
INSERT INTO public.users VALUES (8, 930005125, 'savateeva_zlata');
INSERT INTO public.users VALUES (41, 32370544, 'stepanov_iv_n');


--
-- Name: sites_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sites_id_seq', 76, true);


--
-- Name: system_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.system_settings_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 41, true);


--
-- Name: sites _user_url_uc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sites
    ADD CONSTRAINT _user_url_uc UNIQUE (user_id, url);


--
-- Name: sites sites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sites
    ADD CONSTRAINT sites_pkey PRIMARY KEY (id);


--
-- Name: system_settings system_settings_key_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_key_key UNIQUE (key);


--
-- Name: system_settings system_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_sites_url; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_sites_url ON public.sites USING btree (url);


--
-- Name: ix_sites_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_sites_user_id ON public.sites USING btree (user_id);


--
-- Name: ix_users_telegram_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_telegram_id ON public.users USING btree (telegram_id);


--
-- Name: sites sites_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sites
    ADD CONSTRAINT sites_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

