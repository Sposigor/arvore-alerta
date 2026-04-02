--
-- PostgreSQL database dump
--

-- Dumped from database version 16.3
-- Dumped by pg_dump version 16.3

-- Started on 2026-04-02 11:23:39

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

--
-- TOC entry 5 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO postgres;

--
-- TOC entry 4962 (class 0 OID 0)
-- Dependencies: 5
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 225 (class 1259 OID 25722)
-- Name: clientes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.clientes (
    id bigint NOT NULL,
    nome character varying(100),
    codigo character varying(50)
);


ALTER TABLE public.clientes OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 58494)
-- Name: clientes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.clientes ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.clientes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 231 (class 1259 OID 50302)
-- Name: material; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.material (
    id integer NOT NULL,
    codigo character varying(30) NOT NULL,
    descricao character varying(150) NOT NULL
);


ALTER TABLE public.material OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 50301)
-- Name: material_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.material_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.material_id_seq OWNER TO postgres;

--
-- TOC entry 4963 (class 0 OID 0)
-- Dependencies: 230
-- Name: material_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.material_id_seq OWNED BY public.material.id;


--
-- TOC entry 215 (class 1259 OID 25290)
-- Name: operador; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.operador (
    id bigint NOT NULL,
    nome character varying,
    codigo bigint,
    status boolean
);


ALTER TABLE public.operador OWNER TO postgres;

--
-- TOC entry 216 (class 1259 OID 25295)
-- Name: operador_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.operador_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.operador_id_seq OWNER TO postgres;

--
-- TOC entry 4964 (class 0 OID 0)
-- Dependencies: 216
-- Name: operador_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.operador_id_seq OWNED BY public.operador.id;


--
-- TOC entry 217 (class 1259 OID 25296)
-- Name: ordem_de_producao; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ordem_de_producao (
    id integer NOT NULL,
    numero_op character varying(255),
    quantidade double precision,
    id_produto bigint,
    data_entrega date,
    id_material integer,
    numero_qualidade character varying(50),
    id_tratamento bigint,
    id_cliente integer,
    data_criacao timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    status_id integer DEFAULT 1
);


ALTER TABLE public.ordem_de_producao OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 25301)
-- Name: ordem_de_producao_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ordem_de_producao_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ordem_de_producao_id_seq OWNER TO postgres;

--
-- TOC entry 4965 (class 0 OID 0)
-- Dependencies: 218
-- Name: ordem_de_producao_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ordem_de_producao_id_seq OWNED BY public.ordem_de_producao.id;


--
-- TOC entry 227 (class 1259 OID 25745)
-- Name: processos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.processos (
    id bigint NOT NULL,
    nome character varying(100) NOT NULL
);


ALTER TABLE public.processos OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 25744)
-- Name: processos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.processos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.processos_id_seq OWNER TO postgres;

--
-- TOC entry 4966 (class 0 OID 0)
-- Dependencies: 226
-- Name: processos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.processos_id_seq OWNED BY public.processos.id;


--
-- TOC entry 219 (class 1259 OID 25320)
-- Name: producao; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.producao (
    id bigint NOT NULL,
    dt_inicio timestamp without time zone,
    dt_fim timestamp without time zone,
    status integer,
    qtde_produzida bigint,
    id_operador integer,
    id_ordem_de_producao bigint,
    id_processo bigint NOT NULL,
    id_operador_fim integer
);


ALTER TABLE public.producao OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 25325)
-- Name: producao_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.producao_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.producao_id_seq OWNER TO postgres;

--
-- TOC entry 4967 (class 0 OID 0)
-- Dependencies: 220
-- Name: producao_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.producao_id_seq OWNED BY public.producao.id;


--
-- TOC entry 221 (class 1259 OID 25326)
-- Name: produtos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.produtos (
    id bigint NOT NULL,
    nome character varying,
    codigo character varying(20)
);


ALTER TABLE public.produtos OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 25331)
-- Name: produtos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.produtos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.produtos_id_seq OWNER TO postgres;

--
-- TOC entry 4968 (class 0 OID 0)
-- Dependencies: 222
-- Name: produtos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.produtos_id_seq OWNED BY public.produtos.id;


--
-- TOC entry 233 (class 1259 OID 50329)
-- Name: status; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.status (
    id integer NOT NULL,
    nome character varying(50) NOT NULL
);


ALTER TABLE public.status OWNER TO postgres;

--
-- TOC entry 232 (class 1259 OID 50328)
-- Name: status_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.status_id_seq OWNER TO postgres;

--
-- TOC entry 4969 (class 0 OID 0)
-- Dependencies: 232
-- Name: status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.status_id_seq OWNED BY public.status.id;


--
-- TOC entry 229 (class 1259 OID 25759)
-- Name: tratamentos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tratamentos (
    id bigint NOT NULL,
    nome character varying(100) NOT NULL
);


ALTER TABLE public.tratamentos OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 25758)
-- Name: tratamentos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tratamentos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tratamentos_id_seq OWNER TO postgres;

--
-- TOC entry 4970 (class 0 OID 0)
-- Dependencies: 228
-- Name: tratamentos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tratamentos_id_seq OWNED BY public.tratamentos.id;


--
-- TOC entry 223 (class 1259 OID 25360)
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id bigint NOT NULL,
    setor character varying,
    senha character varying,
    usuario character varying,
    privilegio bigint
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 25365)
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO postgres;

--
-- TOC entry 4971 (class 0 OID 0)
-- Dependencies: 224
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- TOC entry 4742 (class 2604 OID 50305)
-- Name: material id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.material ALTER COLUMN id SET DEFAULT nextval('public.material_id_seq'::regclass);


--
-- TOC entry 4733 (class 2604 OID 25373)
-- Name: operador id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.operador ALTER COLUMN id SET DEFAULT nextval('public.operador_id_seq'::regclass);


--
-- TOC entry 4734 (class 2604 OID 25374)
-- Name: ordem_de_producao id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_de_producao ALTER COLUMN id SET DEFAULT nextval('public.ordem_de_producao_id_seq'::regclass);


--
-- TOC entry 4740 (class 2604 OID 25748)
-- Name: processos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.processos ALTER COLUMN id SET DEFAULT nextval('public.processos_id_seq'::regclass);


--
-- TOC entry 4737 (class 2604 OID 25378)
-- Name: producao id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.producao ALTER COLUMN id SET DEFAULT nextval('public.producao_id_seq'::regclass);


--
-- TOC entry 4738 (class 2604 OID 25379)
-- Name: produtos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.produtos ALTER COLUMN id SET DEFAULT nextval('public.produtos_id_seq'::regclass);


--
-- TOC entry 4743 (class 2604 OID 50332)
-- Name: status id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.status ALTER COLUMN id SET DEFAULT nextval('public.status_id_seq'::regclass);


--
-- TOC entry 4741 (class 2604 OID 25762)
-- Name: tratamentos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tratamentos ALTER COLUMN id SET DEFAULT nextval('public.tratamentos_id_seq'::regclass);


--
-- TOC entry 4739 (class 2604 OID 25385)
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- TOC entry 4947 (class 0 OID 25722)
-- Dependencies: 225
-- Data for Name: clientes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.clientes (id, nome, codigo) FROM stdin;
9	EATON CAXIAS	6
10	EATON VALINHOS	30
11	CUMMINS-MERITOR	37
12	CONFORMETAL	41
13	ZF AUTOMOTIVE	103
\.


--
-- TOC entry 4953 (class 0 OID 50302)
-- Dependencies: 231
-- Data for Name: material; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.material (id, codigo, descricao) FROM stdin;
3	MP180	NBR5915 EEP 1,50X1200X2000
4	MP24	NBR5915 EEP 1,06X1200X2000
5	MP23	NBR5915 EEP 1,06X1200X2000
6	MP3	NBR5906 EP DO 4,00X1200X2000
7	MP5	NBR5906 EP DO 2,55X1200X2000
8	MP115	NBR5007 G2 L590 0,25X230XROLO
9	MP600	NBR6662 SAE 1070 CO 1,00X87XROLO
10	MP882	NBR6662 SAE 1070 TR 0,95X95XROLO
11	MP667	EN10084 2008 16MNCR5 4,00X245X950
\.


--
-- TOC entry 4937 (class 0 OID 25290)
-- Dependencies: 215
-- Data for Name: operador; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.operador (id, nome, codigo, status) FROM stdin;
36	EDNILSON DOS SANTOS	618	\N
\.


--
-- TOC entry 4939 (class 0 OID 25296)
-- Dependencies: 217
-- Data for Name: ordem_de_producao; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ordem_de_producao (id, numero_op, quantidade, id_produto, data_entrega, id_material, numero_qualidade, id_tratamento, id_cliente, data_criacao, status_id) FROM stdin;
85	4582	1000	2381	2026-04-14	7	716492	1	11	2026-03-06 15:24:54.351896	1
78	123	10000	2373	2026-03-18	7	8989	1	11	2026-03-05 10:41:51.312228	3
86	78945	120	2387	2026-03-24	3	4562	3	10	2026-03-06 15:25:45.935732	1
81	7547986	33	2381	2026-07-25	5	4545	2	11	2026-03-05 15:49:46.850449	1
82	123546	1000	2387	2026-03-06	3	123	1	9	2026-03-06 07:39:20.489407	1
87	123456	1000	2376	2026-03-26	9	45874	1	10	2026-03-09 11:36:40.347634	1
88	505050	10000	2379	2026-03-24	3	485695	1	9	2026-03-09 11:41:34.551846	1
79	7812645	10	2386	2026-05-09	8	95136	2	12	2026-03-05 15:20:16.483325	4
89	878745	10000	2387	2026-05-17	3	42671	2	11	2026-03-09 11:42:41.859114	1
80	84632158	44	2376	2026-03-15	3	943682	3	9	2026-03-05 15:46:07.91354	1
91	191919	5000	2381	2026-04-14	5	716492	2	11	2026-03-09 12:43:00.564614	3
90	989898	10000	2389	2026-03-12	5	45856	1	11	2026-03-09 12:40:56.222366	2
84	8678686	10	2381	2026-03-28	3	6866	2	9	2026-03-06 13:35:25.969833	1
83	454544	454	2381	2026-03-10	3	4545	1	9	2026-03-06 11:35:33.719298	1
\.


--
-- TOC entry 4949 (class 0 OID 25745)
-- Dependencies: 227
-- Data for Name: processos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.processos (id, nome) FROM stdin;
2	Estamparia
3	Solda
5	Envio para terceiros
6	Recebimento (terceiros)
1	Materia-Prima
4	Retifica
7	Inspecao final
8	Expedicao
\.


--
-- TOC entry 4941 (class 0 OID 25320)
-- Dependencies: 219
-- Data for Name: producao; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.producao (id, dt_inicio, dt_fim, status, qtde_produzida, id_operador, id_ordem_de_producao, id_processo, id_operador_fim) FROM stdin;
316	2026-03-05 10:42:14.869076	2026-03-05 10:42:53.47755	2	9800	51	78	3	58
317	2026-03-05 15:25:16.222682	2026-03-05 15:29:18.0871	2	10	74	78	1	36
318	2026-03-05 15:29:05.502794	2026-03-05 15:30:11.14668	2	10	53	78	2	59
320	2026-03-05 15:47:16.11394	2026-03-05 15:48:26.459328	2	44	53	80	1	46
321	2026-03-05 15:50:11.859593	2026-03-05 15:50:34.055622	2	31	53	81	2	45
322	2026-03-06 07:41:08.738318	2026-03-06 07:41:55.856031	2	1000	54	82	1	54
323	2026-03-06 07:42:33.64931	2026-03-06 07:43:17.925351	2	950	45	82	2	67
327	2026-03-06 15:27:35.691084	2026-03-06 15:28:15.91902	2	1000	67	85	5	40
328	2026-03-06 15:30:52.080352	2026-03-06 15:31:05.997815	2	1000	46	86	5	43
319	2026-03-05 15:29:48.617904	2026-03-06 15:32:06.225165	2	100	71	78	3	52
329	2026-03-06 15:31:48.363474	2026-03-09 10:29:01.656265	2	10	67	78	8	45
330	2026-03-09 10:29:10.343627	2026-03-09 10:29:20.546351	2	1	46	78	8	58
331	2026-03-09 10:30:07.951971	2026-03-09 10:30:19.293595	2	10	45	84	8	45
332	2026-03-09 10:38:09.537454	2026-03-09 10:38:38.879859	2	10	46	86	2	59
333	2026-03-09 10:38:23.530252	2026-03-09 10:38:50.153531	2	10	63	86	3	40
325	2026-03-06 09:32:48.035769	2026-03-09 10:39:02.499873	2	10	53	81	1	53
324	2026-03-06 07:47:00.635562	2026-03-09 10:39:19.490248	2	10	36	82	3	67
326	2026-03-06 13:35:46.028876	2026-03-09 10:39:54.182057	2	10	53	84	2	67
334	2026-03-09 11:44:09.185172	2026-03-09 11:44:55.738559	2	10000	45	89	2	36
335	2026-03-09 11:47:57.489596	2026-03-09 11:48:29.320604	2	1500	63	89	3	59
336	2026-03-09 12:43:54.433177	2026-03-09 12:44:13.820847	2	4900	45	91	4	46
337	2026-03-09 12:45:25.683092	2026-03-09 12:45:50.421335	2	4800	61	91	3	46
338	2026-03-09 12:47:39.677368	2026-03-09 12:48:00.176433	2	4700	46	91	8	46
339	2026-03-09 12:49:32.143587	\N	1	0	36	90	5	\N
340	2026-03-09 12:50:01.187371	2026-03-09 12:51:18.235157	2	100	46	90	3	46
341	2026-03-09 12:50:57.234968	2026-03-09 12:51:34.721299	2	10	45	84	3	59
\.


--
-- TOC entry 4943 (class 0 OID 25326)
-- Dependencies: 221
-- Data for Name: produtos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.produtos (id, nome, codigo) FROM stdin;
2373	CALÇO	3315960
2374	ANEL ESPACADOR	3315993
2375	TAMPA	3316033
2376	ANEL DE HISTERESE	200C238
2377	TAMPA	3001733
2378	DRIVE STRAP	118C63
2379	SUPORTE DOS CABOS	3004081
2380	DISCO	240C243
2381	ARRUELA	1229W1557
2382	DEFLETOR DE PÓ	3264Z1274
2383	ARRUELA	85166-3
2384	CALCO	28453
2385	FERRAGEM	230148
2386	ESPAÇADOR	47560-330
2387	SUPORTE DE FIXACAO	1346201122
2388	ARRUELA	730103245
2389	SUPORTE	6070301104
\.


--
-- TOC entry 4955 (class 0 OID 50329)
-- Dependencies: 233
-- Data for Name: status; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.status (id, nome) FROM stdin;
2	Em Produção
3	Finalizado
4	Cancelado
1	Aguardando
\.


--
-- TOC entry 4951 (class 0 OID 25759)
-- Dependencies: 229
-- Data for Name: tratamentos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tratamentos (id, nome) FROM stdin;
1	Témico
2	Geral
3	Amostra
4	Não Conforme
\.


--
-- TOC entry 4945 (class 0 OID 25360)
-- Dependencies: 223
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios (id, setor, senha, usuario, privilegio) FROM stdin;
1	\N	$2b$12$P6Tg4mQe70YDibcTZtuW1uwYDDCrFTln2cBEs23hsxZmC5eHnInka	adm	3
98	solda	$2b$12$BVu3famj7mdVvE4ggxTyM.ndXQfUj0WPN9u/Zafq8JgYkCyS7.W8y	solda	1
102	\N	$2b$12$bjCpMVJlbUmztg.I6Plw2ek9hd44yZd2mYMovI4k6B41mm13fDGMe	admin	3
\.


--
-- TOC entry 4972 (class 0 OID 0)
-- Dependencies: 234
-- Name: clientes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.clientes_id_seq', 15, true);


--
-- TOC entry 4973 (class 0 OID 0)
-- Dependencies: 230
-- Name: material_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.material_id_seq', 11, true);


--
-- TOC entry 4974 (class 0 OID 0)
-- Dependencies: 216
-- Name: operador_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.operador_id_seq', 83, true);


--
-- TOC entry 4975 (class 0 OID 0)
-- Dependencies: 218
-- Name: ordem_de_producao_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ordem_de_producao_id_seq', 91, true);


--
-- TOC entry 4976 (class 0 OID 0)
-- Dependencies: 226
-- Name: processos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.processos_id_seq', 8, true);


--
-- TOC entry 4977 (class 0 OID 0)
-- Dependencies: 220
-- Name: producao_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.producao_id_seq', 341, true);


--
-- TOC entry 4978 (class 0 OID 0)
-- Dependencies: 222
-- Name: produtos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.produtos_id_seq', 2390, true);


--
-- TOC entry 4979 (class 0 OID 0)
-- Dependencies: 232
-- Name: status_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.status_id_seq', 4, true);


--
-- TOC entry 4980 (class 0 OID 0)
-- Dependencies: 228
-- Name: tratamentos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tratamentos_id_seq', 1, true);


--
-- TOC entry 4981 (class 0 OID 0)
-- Dependencies: 224
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 102, true);


--
-- TOC entry 4767 (class 2606 OID 58519)
-- Name: clientes clientes_codigo_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clientes
    ADD CONSTRAINT clientes_codigo_unique UNIQUE (codigo);


--
-- TOC entry 4769 (class 2606 OID 25726)
-- Name: clientes clientes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clientes
    ADD CONSTRAINT clientes_pkey PRIMARY KEY (id);


--
-- TOC entry 4777 (class 2606 OID 50309)
-- Name: material material_codigo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.material
    ADD CONSTRAINT material_codigo_key UNIQUE (codigo);


--
-- TOC entry 4779 (class 2606 OID 58517)
-- Name: material material_codigo_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.material
    ADD CONSTRAINT material_codigo_unique UNIQUE (codigo);


--
-- TOC entry 4781 (class 2606 OID 50307)
-- Name: material material_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.material
    ADD CONSTRAINT material_pkey PRIMARY KEY (id);


--
-- TOC entry 4751 (class 2606 OID 50300)
-- Name: ordem_de_producao numero_op_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_de_producao
    ADD CONSTRAINT numero_op_unique UNIQUE (numero_op);


--
-- TOC entry 4745 (class 2606 OID 58522)
-- Name: operador operador_codigo_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.operador
    ADD CONSTRAINT operador_codigo_unique UNIQUE (codigo);


--
-- TOC entry 4747 (class 2606 OID 25401)
-- Name: operador operador_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.operador
    ADD CONSTRAINT operador_pk PRIMARY KEY (id);


--
-- TOC entry 4749 (class 2606 OID 25403)
-- Name: operador operador_un; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.operador
    ADD CONSTRAINT operador_un UNIQUE (codigo);


--
-- TOC entry 4753 (class 2606 OID 25405)
-- Name: ordem_de_producao ordem_de_producao_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_de_producao
    ADD CONSTRAINT ordem_de_producao_pkey PRIMARY KEY (id);


--
-- TOC entry 4771 (class 2606 OID 25752)
-- Name: processos processos_nome_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.processos
    ADD CONSTRAINT processos_nome_key UNIQUE (nome);


--
-- TOC entry 4773 (class 2606 OID 25750)
-- Name: processos processos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.processos
    ADD CONSTRAINT processos_pkey PRIMARY KEY (id);


--
-- TOC entry 4756 (class 2606 OID 25411)
-- Name: producao producao_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.producao
    ADD CONSTRAINT producao_pk PRIMARY KEY (id);


--
-- TOC entry 4759 (class 2606 OID 58507)
-- Name: produtos produtos_codigo_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.produtos
    ADD CONSTRAINT produtos_codigo_unique UNIQUE (codigo);


--
-- TOC entry 4761 (class 2606 OID 25413)
-- Name: produtos produtos_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.produtos
    ADD CONSTRAINT produtos_pk PRIMARY KEY (id);


--
-- TOC entry 4783 (class 2606 OID 50334)
-- Name: status status_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.status
    ADD CONSTRAINT status_pkey PRIMARY KEY (id);


--
-- TOC entry 4775 (class 2606 OID 25764)
-- Name: tratamentos tratamentos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tratamentos
    ADD CONSTRAINT tratamentos_pkey PRIMARY KEY (id);


--
-- TOC entry 4763 (class 2606 OID 58505)
-- Name: produtos unique_codigo; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.produtos
    ADD CONSTRAINT unique_codigo UNIQUE (codigo);


--
-- TOC entry 4765 (class 2606 OID 25425)
-- Name: usuarios usuarios_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pk PRIMARY KEY (id);


--
-- TOC entry 4754 (class 1259 OID 58501)
-- Name: idx_producao_processo_data; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_producao_processo_data ON public.producao USING btree (id_processo, dt_fim);


--
-- TOC entry 4757 (class 1259 OID 58524)
-- Name: produtos_codigo_un; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX produtos_codigo_un ON public.produtos USING btree (codigo);


--
-- TOC entry 4784 (class 2606 OID 50320)
-- Name: ordem_de_producao fk_material; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_de_producao
    ADD CONSTRAINT fk_material FOREIGN KEY (id_material) REFERENCES public.material(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- TOC entry 4789 (class 2606 OID 58496)
-- Name: producao fk_operador_fim; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.producao
    ADD CONSTRAINT fk_operador_fim FOREIGN KEY (id_operador_fim) REFERENCES public.operador(id);


--
-- TOC entry 4785 (class 2606 OID 50285)
-- Name: ordem_de_producao fk_ordem_cliente; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_de_producao
    ADD CONSTRAINT fk_ordem_cliente FOREIGN KEY (id_cliente) REFERENCES public.clientes(id);


--
-- TOC entry 4786 (class 2606 OID 25739)
-- Name: ordem_de_producao fk_ordem_produto; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_de_producao
    ADD CONSTRAINT fk_ordem_produto FOREIGN KEY (id_produto) REFERENCES public.produtos(id);


--
-- TOC entry 4787 (class 2606 OID 25766)
-- Name: ordem_de_producao fk_ordem_tratamento; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_de_producao
    ADD CONSTRAINT fk_ordem_tratamento FOREIGN KEY (id_tratamento) REFERENCES public.tratamentos(id);


--
-- TOC entry 4790 (class 2606 OID 25734)
-- Name: producao fk_producao_ordem; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.producao
    ADD CONSTRAINT fk_producao_ordem FOREIGN KEY (id_ordem_de_producao) REFERENCES public.ordem_de_producao(id);


--
-- TOC entry 4791 (class 2606 OID 25753)
-- Name: producao fk_producao_processo; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.producao
    ADD CONSTRAINT fk_producao_processo FOREIGN KEY (id_processo) REFERENCES public.processos(id);


--
-- TOC entry 4788 (class 2606 OID 50335)
-- Name: ordem_de_producao fk_status; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_de_producao
    ADD CONSTRAINT fk_status FOREIGN KEY (status_id) REFERENCES public.status(id);


--
-- TOC entry 4792 (class 2606 OID 50390)
-- Name: producao producao_fk_4; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.producao
    ADD CONSTRAINT producao_fk_4 FOREIGN KEY (id_operador) REFERENCES public.operador(id);


--
-- TOC entry 4793 (class 2606 OID 50395)
-- Name: producao producao_operador_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.producao
    ADD CONSTRAINT producao_operador_fk FOREIGN KEY (id_operador) REFERENCES public.operador(id);


-- Completed on 2026-04-02 11:23:39

--
-- PostgreSQL database dump complete
--

