"""
Run once to create trivia.db and populate it from the hardcoded DAILY_SETS.
Safe to re-run — it will skip seeding if data already exists.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "trivia.db")

DAILY_SETS = [
    {
        "theme": "Oscar Best Picture Winners",
        "questions": [
            {"question": "This 1994 Tom Hanks film follows a man with a low IQ through pivotal moments in American history.", "answer": "Forrest Gump"},
            {"question": "Directed by James Cameron, this 1997 romance aboard a doomed ocean liner won 11 Academy Awards.", "answer": "Titanic"},
            {"question": "This 2019 Korean thriller by Bong Joon-ho became the first non-English language film to win Best Picture.", "answer": "Parasite"},
        ],
    },
    {
        "theme": "World Capitals",
        "questions": [
            {"question": "This capital city sits on the Danube River and was historically two separate cities: Buda and Pest.", "answer": "Budapest"},
            {"question": "The capital of Iceland, whose name means 'smoky bay' in Old Norse, is the northernmost capital of a sovereign state.", "answer": "Reykjavik"},
            {"question": "This Australian capital was purpose-built as a compromise between Sydney and Melbourne.", "answer": "Canberra"},
        ],
    },
    {
        "theme": "Classic Rock Legends",
        "questions": [
            {"question": "This British band, fronted by Freddie Mercury, is known for 'Bohemian Rhapsody' and 'We Will Rock You.'", "answer": "Queen"},
            {"question": "This band, featuring Jimmy Page on guitar, recorded 'Stairway to Heaven' in 1971.", "answer": "Led Zeppelin"},
            {"question": "Known as 'The Boss,' this New Jersey rocker released 'Born to Run' in 1975.", "answer": "Bruce Springsteen"},
        ],
    },
    {
        "theme": "Famous Scientists",
        "questions": [
            {"question": "This physicist developed the theory of general relativity and won the 1921 Nobel Prize in Physics.", "answer": "Albert Einstein"},
            {"question": "This Polish-French scientist was the first woman to win a Nobel Prize and the first person to win it in two different sciences.", "answer": "Marie Curie"},
            {"question": "This English naturalist published 'On the Origin of Species' in 1859, introducing the theory of natural selection.", "answer": "Charles Darwin"},
        ],
    },
    {
        "theme": "Shakespeare Plays",
        "questions": [
            {"question": "This tragedy features a Danish prince who delivers the famous soliloquy beginning 'To be or not to be.'", "answer": "Hamlet"},
            {"question": "This comedy features the mischievous fairy Puck and concludes with multiple weddings in an enchanted forest.", "answer": "A Midsummer Night's Dream"},
            {"question": "This history play opens with the line 'Now is the winter of our discontent' from a scheming royal.", "answer": "Richard III"},
        ],
    },
    {
        "theme": "Famous Painters",
        "questions": [
            {"question": "This Dutch post-impressionist created 'Starry Night' and 'Sunflowers' but sold only one painting in his lifetime.", "answer": "Vincent van Gogh"},
            {"question": "This Spanish surrealist painted 'The Persistence of Memory,' featuring melting clocks in a dreamlike landscape.", "answer": "Salvador Dalí"},
            {"question": "This Italian Renaissance artist painted the ceiling of the Sistine Chapel over four years.", "answer": "Michelangelo"},
        ],
    },
    {
        "theme": "Space Missions",
        "questions": [
            {"question": "This 1969 NASA mission carried the first humans to land on the Moon.", "answer": "Apollo 11"},
            {"question": "Launched in 1990, this space telescope orbiting Earth has captured images of objects billions of light-years away.", "answer": "Hubble Space Telescope"},
            {"question": "Launched in 1977, this NASA probe is now the farthest human-made object from Earth, traveling in interstellar space.", "answer": "Voyager 1"},
        ],
    },
    {
        "theme": "Dystopian Classics",
        "questions": [
            {"question": "George Orwell's 1949 novel features Big Brother, Room 101, and the Thought Police.", "answer": "1984"},
            {"question": "Aldous Huxley's 1932 novel depicts a future society where humans are genetically engineered and pleasure-conditioned.", "answer": "Brave New World"},
            {"question": "Margaret Atwood's 1985 novel is set in the theocratic Republic of Gilead, where women are enslaved as handmaidens.", "answer": "The Handmaid's Tale"},
        ],
    },
    {
        "theme": "Famous Inventors",
        "questions": [
            {"question": "This American inventor held over 1,000 patents, including the phonograph and a practical incandescent light bulb.", "answer": "Thomas Edison"},
            {"question": "This Scottish-American inventor is credited with patenting the first practical telephone in 1876.", "answer": "Alexander Graham Bell"},
            {"question": "These two Ohio brothers made the first successful powered airplane flight at Kitty Hawk in 1903.", "answer": "Wright Brothers"},
        ],
    },
    {
        "theme": "Nobel Peace Prize Winners",
        "questions": [
            {"question": "This South African anti-apartheid leader shared the Nobel Peace Prize in 1993 and later became his country's president.", "answer": "Nelson Mandela"},
            {"question": "This Catholic nun founded the Missionaries of Charity and won the Nobel Peace Prize in 1979.", "answer": "Mother Teresa"},
            {"question": "Shot by the Taliban for advocating girls' education, this Pakistani activist became the youngest Nobel Peace laureate.", "answer": "Malala Yousafzai"},
        ],
    },
    {
        "theme": "Famous Philosophers",
        "questions": [
            {"question": "This ancient Greek philosopher, teacher of Plato, was sentenced to death by drinking hemlock.", "answer": "Socrates"},
            {"question": "This German philosopher wrote 'Thus Spoke Zarathustra' and is known for the declaration 'God is dead.'", "answer": "Friedrich Nietzsche"},
            {"question": "This French philosopher is most commonly known for his philosophical statement 'cogito, ergo sum'.", "answer": "Rene Descartes"},
        ],
    },
    {
        "theme": "World Mountains",
        "questions": [
            {"question": "This Himalayan peak on the Nepal-Tibet border is the highest mountain on Earth.", "answer": "Mount Everest"},
            {"question": "This dormant volcano in Tanzania is the highest peak in Africa.", "answer": "Mount Kilimanjaro"},
            {"question": "This iconic pyramid-shaped peak on the border of Switzerland and Italy is one of the Alps' most recognized summits.", "answer": "Matterhorn"},
        ],
    },
    {
        "theme": "Famous Composers",
        "questions": [
            {"question": "This German composer wrote his Ninth Symphony, including 'Ode to Joy,' while completely deaf.", "answer": "Ludwig van Beethoven"},
            {"question": "This Austrian prodigy composed over 600 works, including 'The Magic Flute' and 'Symphony No. 40.'", "answer": "Wolfgang Amadeus Mozart"},
            {"question": "This Russian composer wrote the ballets 'Swan Lake,' 'The Nutcracker,' and 'Sleeping Beauty.'", "answer": "Pyotr Ilyich Tchaikovsky"},
        ],
    },
    {
        "theme": "Famous Explorers",
        "questions": [
            {"question": "This Portuguese explorer led the first circumnavigation of the globe, though he died before it was completed.", "answer": "Ferdinand Magellan"},
            {"question": "This Italian navigator, sailing under the Spanish crown in 1492, made contact with the Americas.", "answer": "Christopher Columbus"},
            {"question": "This Norwegian explorer led the first expedition to reach the South Pole in December 1911.", "answer": "Roald Amundsen"},
        ],
    },
    {
        "theme": "Iconic TV Shows",
        "questions": [
            {"question": "This AMC drama follows a high school chemistry teacher who transforms into a methamphetamine manufacturer.", "answer": "Breaking Bad"},
            {"question": "This HBO fantasy epic, based on George R.R. Martin's novels, is set in the fictional land of Westeros.", "answer": "Game of Thrones"},
            {"question": "This NBC mockumentary, set in a Scranton, Pennsylvania paper company, follows quirky office workers.", "answer": "The Office"},
        ],
    },
    {
        "theme": "Legendary Athletes",
        "questions": [
            {"question": "This Chicago Bulls star won six NBA championships in the 1990s and is nicknamed 'Air Jordan.'", "answer": "Michael Jordan"},
            {"question": "This American tennis player won 23 Grand Slam singles titles, the most of any player in the Open Era.", "answer": "Serena Williams"},
            {"question": "This Jamaican sprinter won the 100m and 200m at three consecutive Olympics, earning the title 'fastest man alive.'", "answer": "Usain Bolt"},
        ],
    },
    {
        "theme": "Seven Wonders of the Ancient World",
        "questions": [
            {"question": "The only surviving wonder of the ancient world, this structure in Egypt was built as a royal tomb.", "answer": "Great Pyramid of Giza"},
            {"question": "This wonder was said to be a series of tiered gardens built in ancient Babylon by King Nebuchadnezzar II.", "answer": "Hanging Gardens of Babylon"},
            {"question": "This massive bronze statue guarded the entrance to the harbor of a Greek island city.", "answer": "Colossus of Rhodes"},
        ],
    },
    {
        "theme": "Famous Mathematicians",
        "questions": [
            {"question": "This ancient Greek scholar wrote 'Elements,' a foundational text in geometry still studied today.", "answer": "Euclid"},
            {"question": "This prolific 18th-century Swiss mathematician introduced the notation 'e' and 'i' and published more papers than any other mathematician.", "answer": "Leonhard Euler"},
            {"question": "This largely self-taught Indian mathematician made extraordinary contributions to number theory with minimal formal training.", "answer": "Srinivasa Ramanujan"},
        ],
    },
    {
        "theme": "Iconic 90s Films",
        "questions": [
            {"question": "This 1999 Wachowski sci-fi film features Neo discovering that reality is a computer simulation.", "answer": "The Matrix"},
            {"question": "This 1994 Quentin Tarantino film weaves interconnected stories involving hitmen, a boxer, and a gangster's wife.", "answer": "Pulp Fiction"},
            {"question": "This 1993 Steven Spielberg film depicts Oskar Schindler's rescue of over 1,000 Jewish people during the Holocaust.", "answer": "Schindler's List"},
        ],
    },
    {
        "theme": "Famous Poets",
        "questions": [
            {"question": "Known as the 'Belle of Amherst,' this American poet wrote nearly 1,800 poems but published fewer than a dozen in her lifetime.", "answer": "Emily Dickinson"},
            {"question": "This Romantic poet wrote 'Ode to a Nightingale' and 'To Autumn' before dying of tuberculosis at just 25.", "answer": "John Keats"},
            {"question": "This Chilean poet, author of 'Twenty Love Poems and a Song of Despair,' won the Nobel Prize in Literature in 1971.", "answer": "Pablo Neruda"},
        ],
    },
    {
        "theme": "Elements of the Periodic Table",
        "questions": [
            {"question": "This precious metal, symbol Au from the Latin 'aurum,' is element number 79.", "answer": "Gold"},
            {"question": "With the symbol Hg, this metal is the only one that is liquid at room temperature.", "answer": "Mercury"},
            {"question": "The lightest element, symbol H, makes up about 75% of all normal matter in the universe by mass.", "answer": "Hydrogen"},
        ],
    },
    {
        "theme": "Famous Architects",
        "questions": [
            {"question": "This Catalan architect designed the still-unfinished Sagrada Família basilica in Barcelona.", "answer": "Antoni Gaudí"},
            {"question": "This American architect designed Fallingwater, a house built over a waterfall in rural Pennsylvania.", "answer": "Frank Lloyd Wright"},
            {"question": "This Chinese-American architect designed the iconic glass pyramid entrance to the Louvre Museum in Paris.", "answer": "I.M. Pei"},
        ],
    },
    {
        "theme": "Mythological Figures",
        "questions": [
            {"question": "In Greek mythology, this hero completed twelve labors assigned by King Eurystheus.", "answer": "Hercules"},
            {"question": "This Norse god of thunder wields the hammer Mjölnir and is associated with storms and strength.", "answer": "Thor"},
            {"question": "In Egyptian mythology, this jackal-headed deity was the god of the dead and guide of souls.", "answer": "Anubis"},
        ],
    },
    {
        "theme": "Grammy Album of the Year",
        "questions": [
            {"question": "This Adele album, featuring 'Rolling in the Deep' and 'Someone Like You,' won Grammy Album of the Year in 2012.", "answer": "21"},
            {"question": "This Taylor Swift album, featuring 'Shake It Off' and 'Blank Space,' won Grammy Album of the Year in 2016.", "answer": "1989"},
            {"question": "This debut album by Billie Eilish won Grammy Album of the Year in 2020, making her the youngest artist to do so.", "answer": "When We All Fall Asleep Where Do We Go"},
        ],
    },
    {
        "theme": "World Rivers",
        "questions": [
            {"question": "Flowing through northeastern Africa and Egypt, this river is traditionally considered the longest in the world.", "answer": "Nile"},
            {"question": "This South American river carries more water than any other river on Earth.", "answer": "Amazon"},
            {"question": "Flowing through Germany and the Netherlands into the North Sea, this river is one of Europe's busiest waterways.", "answer": "Rhine"},
        ],
    },
    {
        "theme": "Classic Video Games",
        "questions": [
            {"question": "This 1985 Nintendo side-scroller features a plumber jumping on enemies to rescue Princess Peach from Bowser.", "answer": "Super Mario Bros"},
            {"question": "This acclaimed 1998 Nintendo 64 adventure game stars Link navigating the land of Hyrule across time.", "answer": "The Legend of Zelda Ocarina of Time"},
            {"question": "This 1993 id Software first-person shooter, set on a Martian moon, is credited with popularizing the FPS genre.", "answer": "Doom"},
        ],
    },
    {
        "theme": "Classic Novels",
        "questions": [
            {"question": "This 1851 Herman Melville novel follows Captain Ahab's obsessive hunt for a great white whale.", "answer": "Moby Dick"},
            {"question": "Jane Austen's 1813 novel follows Elizabeth Bennet and the brooding Mr. Darcy overcoming misunderstandings.", "answer": "Pride and Prejudice"},
            {"question": "This sweeping Leo Tolstoy epic follows Russian nobility against the backdrop of Napoleon's 1812 invasion.", "answer": "War and Peace"},
        ],
    },
    {
        "theme": "US Presidents",
        "questions": [
            {"question": "The only president to serve more than two terms, this leader guided the US through the Great Depression and World War II.", "answer": "Franklin D. Roosevelt"},
            {"question": "This 16th president issued the Emancipation Proclamation and was assassinated at Ford's Theatre in 1865.", "answer": "Abraham Lincoln"},
            {"question": "The youngest person ever elected president, this leader was the first Catholic to hold the office.", "answer": "John F. Kennedy"},
        ],
    },
    {
        "theme": "Olympic Host Cities",
        "questions": [
            {"question": "This Greek city hosted the first modern Olympic Games in 1896 and again a century later in 2004.", "answer": "Athens"},
            {"question": "This Japanese city hosted the 1964 Summer Olympics, becoming the first Asian city to do so.", "answer": "Tokyo"},
            {"question": "This Brazilian city hosted the 2016 Summer Olympics, the first held in South America.", "answer": "Rio de Janeiro"},
        ],
    },
    {
        "theme": "Literary Giants",
        "questions": [
            {"question": "This Colombian author wrote 'One Hundred Years of Solitude' and won the Nobel Prize in Literature in 1982.", "answer": "Gabriel García Márquez"},
            {"question": "This Russian novelist wrote 'Crime and Punishment' and 'The Brothers Karamazov.'", "answer": "Fyodor Dostoevsky"},
            {"question": "This American author wrote 'The Old Man and the Sea,' winning the Pulitzer Prize in 1953.", "answer": "Ernest Hemingway"},
        ],
    },
]


def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS daily_sets (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            theme   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS questions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id      INTEGER NOT NULL REFERENCES daily_sets(id) ON DELETE CASCADE,
            sort_order  INTEGER NOT NULL DEFAULT 0,
            question    TEXT NOT NULL,
            answer      TEXT NOT NULL
        );
    """)


def seed(conn):
    count = conn.execute("SELECT COUNT(*) FROM daily_sets").fetchone()[0]
    if count > 0:
        print(f"Database already has {count} sets — skipping seed.")
        return

    for ds in DAILY_SETS:
        cur = conn.execute("INSERT INTO daily_sets (theme) VALUES (?)", (ds["theme"],))
        set_id = cur.lastrowid
        for i, q in enumerate(ds["questions"]):
            conn.execute(
                "INSERT INTO questions (set_id, sort_order, question, answer) VALUES (?, ?, ?, ?)",
                (set_id, i, q["question"], q["answer"]),
            )

    conn.commit()
    print(f"Seeded {len(DAILY_SETS)} daily sets into {DB_PATH}")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    seed(conn)
    conn.close()
