create_table_commands = (
            """CREATE TABLE "Subject" (
                    id                           serial not null primary key,
                    name                         text   not null,
                    descriptive_name             text   not null,
                    catalog_number               text   not null,
                    description                  text   not null,
                    catalog_topic                text,
                    catalog_description          text,
                    credits                      text,
                    academic_org                 text,
                    academic_org_short_desc      text,
                    reporting_college            text,
                    reporting_college_short_desc text,
                    reporting_org                text,
                    reporting_org_short_desc     text
                    );
            """,
            """ CREATE TABLE "Instructor" (
                    id          serial not null primary key,
                    faculty_id  text,
                    first_name  text   not null,
                    middle_name text,
                    last_name   text   not null
                    );
            """,
            """ CREATE TABLE "Grade" (
                    id              serial  not null primary key,
                    instructor_id   integer not null references "Instructor"(id),
                    total_enrolled  integer,
                    "A"             integer,
                    "B"             integer,
                    "C"             integer,
                    "D"             integer,
                    "F"             integer,
                    "O"             integer
                    );
            """,
            """CREATE TABLE "EvaluationScore" (
                    id       serial not null primary key,
                    question text   not null,
                    "1"      integer,
                    "2"      integer,
                    "3"      integer,
                    "4"      integer,
                    "5"      integer,
                    "N/A"    integer
            );
            """,
            """CREATE TABLE "Evaluation" (
                    id               serial  not null primary key,
                    instructor_id    integer not null references "Instructor"(id),
                    invited_count    integer,
                    respondent_count integer,
                    "Q1"             integer not null references "EvaluationScore"(id),
                    "Q2"             integer not null references "EvaluationScore"(id),
                    "Q3"             integer not null references "EvaluationScore"(id),
                    "Q4"             integer not null references "EvaluationScore"(id),
                    "Q5"             integer not null references "EvaluationScore"(id),
                    "Q6"             integer not null references "EvaluationScore"(id),
                    "Q7"             integer not null references "EvaluationScore"(id),
                    "Q8"             integer not null references "EvaluationScore"(id),
                    "Q9"             integer not null references "EvaluationScore"(id),
                    "Q10"            integer not null references "EvaluationScore"(id),
                    "Q11"            integer not null references "EvaluationScore"(id),
                    "Q12"            integer not null references "EvaluationScore"(id),
                    "Q13"            integer not null references "EvaluationScore"(id),
                    "Q14"            integer not null references "EvaluationScore"(id),
                    "Q15"            integer not null references "EvaluationScore"(id),
                    "Q16"            integer not null references "EvaluationScore"(id),
                    "Q17"            integer not null references "EvaluationScore"(id),
                    "Q18"            integer not null references "EvaluationScore"(id),
                    "Q19"            integer not null references "EvaluationScore"(id),
                    "Q20"            integer not null references "EvaluationScore"(id),
                    "Q21"            integer not null references "EvaluationScore"(id),
                    "Q22"            integer not null references "EvaluationScore"(id),
                    "Q23"            integer not null references "EvaluationScore"(id),
                    "Q24"            integer not null references "EvaluationScore"(id),
                    "Q25"            integer not null references "EvaluationScore"(id),
                    "Q26"            integer not null references "EvaluationScore"(id),
                    "Q27"            integer not null references "EvaluationScore"(id),
                    "Q28"            integer not null references "EvaluationScore"(id),
                    "Q29"            integer not null references "EvaluationScore"(id),
                    "Q30"            integer not null references "EvaluationScore"(id),
                    "Q31"            integer not null references "EvaluationScore"(id),
                    "Q32"            integer not null references "EvaluationScore"(id)
            );
            """,
            """ CREATE TABLE "Course" (
                    id              serial  not null primary key,
                    subject_id      integer not null references "Subject"(id),
                    instructor_id   integer not null references "Instructor"(id),
                    grade_id        integer not null references "Grade"(id),
                    evaluation_id   integer not null references "Evaluation"(id),
                    class_number    text    not null,
                    section         text    not null,
                    term            integer not null,
                    semester        text    not null,
                    session_code    text    not null,
                    course_level    integer,
                    total_enrolled  integer
            );
            """,
            """CREATE TABLE "User" (
                    id       serial not null primary key,
                    username text   not null unique,
                    email    text   unique,
                    password text   not null,
                    token    text,
                    date_created timestamp
            );
              """,
            """CREATE TABLE "Review" (
                    id             serial   not null primary key,
                    body           text     not null,
                    rating         integer  not null,
                    grade          text     not null,
                    approved       integer  not null default 0,
                    user_id        integer  not null references "User"(id),
                    subject_id     integer  references "Subject"(id),
                    instructor_id  integer  references "Instructor"(id),
                    faculty_id     text     not null,
                    date_created   timestamp not null,
                    last_updated   timestamp
            );
             """,
            """CREATE TABLE "Analytics" (
                    id              serial not null,
                    subject_id      integer references "Subject"(id),
                    instructor_id   integer references "Instructor"(id),
                    user_id         integer references "User"(id),
                    date_created    timestamp not null
            );
               """
        );