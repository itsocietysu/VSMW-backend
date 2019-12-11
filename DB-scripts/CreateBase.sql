DROP SEQUENCE IF EXISTS vsmw_seq;
CREATE SEQUENCE vsmw_seq start with 1 increment by 1;

DROP TABLE IF EXISTS "vsmw_session";
CREATE TABLE "vsmw_session" (
	"vid" BIGSERIAL NOT NULL PRIMARY KEY,
	"title" VARCHAR(256) NOT NULL,
	"type" VARCHAR(256) NOT NULL,
	"image" VARCHAR(4000) NOT NULL,
	"created" TIMESTAMP WITH TIME ZONE NOT NULL,
	"updated" TIMESTAMP WITH TIME ZONE NOT NULL,
	"expires" TIMESTAMP WITH TIME ZONE NOT NULL
) WITH (
  OIDS=FALSE
);

DROP TABLE IF EXISTS "vsmw_curr_session";
CREATE TABLE "vsmw_curr_session" (
	"curr_id" BIGSERIAL NOT NULL PRIMARY KEY
) WITH (
  OIDS=FALSE
);
INSERT INTO vsmw_curr_session VALUES (1);

DROP TABLE IF EXISTS "vsmw_user";
CREATE TABLE "vsmw_user" (
	"vid" BIGSERIAL NOT NULL PRIMARY KEY,
	"fingerprint" VARCHAR(256) NOT NULL UNIQUE
) WITH (
  OIDS=FALSE
);

DROP TABLE IF EXISTS "vsmw_vote";
CREATE TABLE "vsmw_vote" (
	"session" BIGSERIAL NOT NULL,
	"user" VARCHAR(256) NOT NULL,
	"value" INT NOT NULL,
	PRIMARY KEY (session, "user")
) WITH (
  OIDS=FALSE
);

commit;
