import spacy
import requests
from textblob import TextBlob
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer, util
import concurrent.futures

# Concept alias map
# Manually defined related terms. If a user searches for "Python", also search for loops, variables, syntax etc.
# This helps the system match resources even if the exact keyword isn't present.
CONCEPT_ALIASES = {
    # Computer Systems
    "cpu": ["control unit", "alu", "registers", "fetch-decode-execute", "FDE", "clock speed", "cores"],
    "memory": ["RAM", "ROM", "virtual memory", "cache", "flash memory", "secondary storage", "solid state", "optical"],
    "software": ["operating systems", "utility software", "file management", "encryption software"],

    # Data Representation
    "binary": ["bit", "byte", "nibble", "base 2", "denary", "binary addition", "binary shifts", "overflow", "place value", "two's complement"],
    "hexadecimal": ["hex", "base 16", "binary conversion", "memory addresses", "colour codes"],
    "ascii": ["character sets", "binary code", "unicode", "encoding"],
    "image": ["pixel", "resolution", "colour depth", "bitmap", "metadata"],
    "sound": ["sampling", "sample rate", "sample resolution", "bit depth", "file size"],
    "compression": ["lossy", "lossless", "run length encoding", "RLE", "huffman coding"],
    "kb": ["kib", "kilobyte", "kibibyte"],
    "mb": ["mib", "megabyte", "mebibyte"],
    "gb": ["gib", "gigabyte", "gibibyte"],
    "tb": ["tib", "terabyte", "tebibyte"],
    "pb": ["pib", "petabyte", "pebibyte"],

    # Boolean Logic
    "logic": ["truth tables", "AND", "OR", "NOT", "logic gates", "circuit diagrams", "boolean"],

    # Algorithmic Thinking
    "algorithm": ["sorting", "searching", "binary search", "linear search", "merge sort", "bubble sort", "efficiency", "inputs", "outputs"],

    # Programming
    "python": ["code", "variables", "loops", "syntax", "functions", "exceptions", "strings", "interpreter", "file handling", "data types"],
    "programming": ["pseudocode", "flowcharts", "compiler", "debugging", "testing", "iteration", "procedures", "subroutines", "modular code", "trace tables"],

    # Databases
    "database": ["SQL", "MySQL", "tables", "records", "fields", "schema", "normalisation", "primary key", "foreign key", "relationships", "data types"],

    # Productivity Software
    "spreadsheet": ["cells", "formulas", "functions", "charts", "modelling", "conditional formatting"],
    "word processor": ["templates", "styles", "mail merge", "text formatting", "headers", "footers"],
    "presentation": ["slides", "transitions", "animations", "speaker notes"],

    # Solution Development
    "development": ["requirements", "design", "implementation", "evaluation", "maintenance", "iteration", "inputs", "outputs"],

    # Testing
    "testing": ["test data", "normal data", "boundary data", "invalid data", "dry run", "syntax error", "logic error", "runtime error", "debugging tools"],

    # Computer Networks
    "networking": ["LAN", "WAN", "topologies", "protocols", "IP", "MAC address", "packets", "client server", "peer to peer", "ethernet", "WiFi", "DNS", "cloud"],

    # Security
    "cybersecurity": ["malware", "phishing", "brute force", "social engineering", "firewall", "penetration testing", "passwords", "encryption", "anti-virus", "two-factor authentication"],

    # Impacts
    "ethics": ["data protection", "GDPR", "bias", "accessibility", "sustainability", "automation", "employment"],

    # Digital Authoring
    "digital authoring": ["web design", "HTML", "CSS", "multimedia", "navigation", "UX", "UI", "responsive design"],

    # Electronics
    "electronics": ["circuits", "transistors", "resistors", "sensors", "input devices", "output devices", "microcontrollers"]
}

# Whitelist of words that TextBlob is incorrectly changing - add to list as more appear in testing
COMMON_WORDS = {"what", "denary"}

def correct_spelling(text: str) -> str:
    corrected_words = []
    for word in text.split():
        # Only correct if the word is not in your common word list
        if word.lower() in COMMON_WORDS:
            corrected_words.append(word)
        else:
            corrected_words.append(str(TextBlob(word).correct()))

    return " ".join(corrected_words)

class NLPProcessor:
    def __init__(self):
        # Load spaCy for tokenisation and lemmatisation
        self.spacy_model = spacy.load("en_core_web_md")
        # Load a sentence transformer for semantic similarity
        self.semantic_model = SentenceTransformer("all-MiniLM-L6-v2")

    def preprocess_query(self, query: str) -> (List[str], str):
        """
        Preprocess the user's search query.
        - Tokenises and lemmatises the input using spaCy
        - Removes punctuation and stopwords
        - Expands known keywords using CONCEPT_ALIASES
        Returns: (expanded keyword list, original query)
        """
        doc = self.spacy_model(query.lower())
        tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]

        expanded = set(tokens)
        for token in tokens:
            expanded.update(CONCEPT_ALIASES.get(token, []))

        return list(expanded), query

    def fetch_json_data(self, url: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Generic helper to fetch JSON data from a URL.
        Returns parsed JSON or an empty list on error.
        """
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[Error] Fetching data from {url}: {e}")
            return []

    def filter_and_rank_outcomes(
            self,
            data: List[Dict[str, Any]],
            expanded_terms: List[str],
            original_query: str,
            strong_threshold: float = 1.0,
            related_threshold: float = 0.7,
            semantic_weight: float = 1.0,
            keyword_weight: float = 0.4
    ) -> Dict[str, Any]:
        """
        Filters and ranks learning outcomes using:
        - Semantic similarity (via sentence transformer)
        - Direct keyword matching
        Batches term embeddings to improve performance.
        Returns:
            - A list of strong matches
            - A list of related matches
            - Metadata dictionary: outcome_id → {score, matched_terms}
        """
        strong_matches, related_matches = [], []
        outcome_metadata = {}
        seen_ids = set()

        # DEBUG
        print("Original query:", original_query)
        print("Expanded terms:", expanded_terms)

        # STEP 1: Batch encode all expanded query term
        # This avoids encoding each word individually in the loop
        # It returns a tensor matrix of embeddings for each term in expanded_terms

        # If the expanded query terms are empty or contain only blank strings, then it cannot generate embeddings (would return a tensor with invalid shape)
        # This prevents the NLP pipeline from crashing downstream during similarity scoring
        if not expanded_terms or all(not term.strip() for term in expanded_terms):
            raise ValueError("Expanded terms are empty or unusable - skipping NLP.")

        term_embeddings = self.semantic_model.encode(expanded_terms, convert_to_tensor=True)

        # DEBUG
        print("Term embeddings shape:", term_embeddings.shape)
        print("Type of expanded_terms:", type(expanded_terms))

        # STEP 2: Loop through every learning outcome from the dataset
        for item in data:
            outcome_id = item.get("outcome_id")
            if not outcome_id or outcome_id in seen_ids:
                continue  # Skip duplicates or missing IDs

            outcome_text = item.get("outcome", "").lower()
            if not outcome_text:
                # Skip empty outcome descriptions
                continue

            # STEP 3: Encode the outcome text
            outcome_embedding = self.semantic_model.encode(outcome_text, convert_to_tensor=True)

            # STEP 4: Compute semantic similarity to each query term (batched)
            # This gives a vector of similarity scores; take the highest (most relevant)
            similarities = util.cos_sim(term_embeddings, outcome_embedding)
            semantic_score = float(similarities.max().item())

            # STEP 5: Compute keyword match score
            keyword_hits = sum(term in outcome_text for term in expanded_terms)
            matched_terms = [term for term in expanded_terms if term in outcome_text]

            # STEP 6: Combine both scores into a total relevance score
            total_score = round((semantic_score * semantic_weight) + (keyword_hits * keyword_weight), 3)

            # Attach metadata to the outcome
            item["score"] = total_score
            item["matched_terms"] = matched_terms
            outcome_metadata[outcome_id] = {
                "score": total_score,
                "matched_terms": matched_terms,
                "outcome_text": item.get("outcome")
            }

            seen_ids.add(outcome_id)

            # STEP 7: Categorise into strong or related
            if total_score >= strong_threshold:
                strong_matches.append(item)
            elif total_score >= related_threshold:
                related_matches.append(item)

        # STEP 8: Return sorted top matches and metadata
        return {
            "strong_matches": sorted(strong_matches, key=lambda x: x["score"], reverse=True)[:10],
            "related_matches": sorted(related_matches, key=lambda x: x["score"], reverse=True)[:10],
            "metadata": outcome_metadata
        }


    def get_learning_content(self,
                             outcomes: List[Dict[str, Any]],
                             material_type: str,
                             headers: Dict[str, str],
                             metadata: Dict = None) -> List[Dict[str, Any]]:
        """
        Fetches content (learning, test, or exam) for each outcome.
        Runs HTTP requests in parallel using ThreadPoolExecutor which is much faster than sequential fetching, especially when many matches are returned.
        """
        def fetch_content(item):
            """
            Internal helper function to fetch data for one outcome_id.
            Returns the first content item (or None if failed).
            """
            outcome_id = item.get("outcome_id")
            if not outcome_id:
                return None
            url = f"https://bit-by-bit.org/api/{material_type}?_format=json&outcome_id={outcome_id}"
            data = self.fetch_json_data(url, headers)
            if data:
                # Attach outcome_id to the item
                data[0]["outcome_id"] = outcome_id
                # Attach outcome_text from metadata if available
                if metadata and outcome_id in metadata:
                    data[0]["outcome_text"] = metadata[outcome_id].get("outcome_text")

                return data[0]
            return None

        # Run the fetches in parallel across threads
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(fetch_content, outcomes))

        # Filter out any failed or None responses
        return [r for r in results if r]

    def get_hyperlinked_content(self, content: List[Dict[str, Any]], metadata: Dict[int, Dict[str, Any]] = None) -> Dict[int, Dict[str, Any]]:
        """
        Enhances each content item with match metadata and prerequisite links.
        Returns a dict keyed by content ID, with additional fields for UI display.
        """
        hyperlinked = {}
        seen = set()
        id_map = {item.get("id"): item for item in content if item.get("id")}

        for item in content:
            item_id = item.get("id")
            title = item.get("title")
            url = item.get("url")
            teaser = item.get("teaser")
            content_type = item.get("type")
            prerequisites = item.get("prerequisite_learning_id", [])

            if not title or not url or (title, url) in seen:
                continue
            seen.add((title, url))

            prereq_links = []
            for pid in prerequisites:
                prereq = id_map.get(pid)
                if prereq:
                    prereq_links.append({
                        "title": prereq.get("title"),
                        "url": prereq.get("url")
                    })

            outcome_id = item.get("outcome_id")
            score = metadata.get(outcome_id, {}).get("score") if metadata else None
            matched_terms = metadata.get(outcome_id, {}).get("matched_terms", []) if metadata else []

            hyperlinked[item_id] = {
                "title": title,
                "url": url,
                "type": content_type,
                "teaser": teaser,
                "prerequisites": prereq_links,
                "score": score,
                "matched_terms": matched_terms,
                "outcome_id": outcome_id,
                "outcome_text": item.get("outcome_text")
            }

        return hyperlinked

# Example test
if __name__ == "__main__":
    # User query to test the system
    query = "I want to learn Python"

    # Standard headers required by the Bit-by-Bit API
    headers = {"User-Agent": "Mozilla/5.0"}

    # Instantiate the processor
    processor = NLPProcessor()

    # Step 1: Preprocess the query and expand it using known aliases
    expanded_terms, original_query = processor.preprocess_query(query)
    print(f"\nExpanded terms: {expanded_terms}\n")

    # Step 2: Fetch the full list of learning outcomes
    outcomes_url = "https://bit-by-bit.org/api/learning-outcomes?_format=json"
    all_outcomes = processor.fetch_json_data(outcomes_url, headers)

    # Step 3: Rank outcomes based on smart scoring (semantic + keyword)
    matches = processor.filter_and_rank_outcomes(
        all_outcomes,
        expanded_terms,
        original_query
    )

    strong = matches["strong_matches"]
    related = matches["related_matches"]
    metadata = matches["metadata"]

    print(f"[INFO] Strong matches found: {len(strong)}")
    print(f"[INFO] Related matches found: {len(related)}\n")

    # Step 4: Fetch 3 types of content per outcome: learning, self-test, and exam questions
    learning_strong = processor.get_learning_content(strong, "learning-by-outcome", headers)
    testing_strong = processor.get_learning_content(strong, "self-test-by-outcome", headers)
    exam_strong = processor.get_learning_content(strong, "gcse-questions-by-outcome", headers)

    learning_related = processor.get_learning_content(related, "learning-by-outcome", headers)
    testing_related = processor.get_learning_content(related, "self-test-by-outcome", headers)
    exam_related = processor.get_learning_content(related, "gcse-questions-by-outcome", headers)

    # Step 5: Attach metadata and convert content to a display-friendly format
    result_learning_strong = processor.get_hyperlinked_content(learning_strong, metadata)
    result_testing_strong = processor.get_hyperlinked_content(testing_strong, metadata)
    result_exam_strong = processor.get_hyperlinked_content(exam_strong, metadata)

    result_learning_related = processor.get_hyperlinked_content(learning_related, metadata)
    result_testing_related = processor.get_hyperlinked_content(testing_related, metadata)
    result_exam_related = processor.get_hyperlinked_content(exam_related, metadata)

    # Step 6: Merge different types of content into a single structure per outcome
    def merge_content_by_outcome(learning, test, exam):
        """
        Groups learning, test, and exam resources under the same outcome_id.
        Each entry contains all resource types + metadata.
        """
        merged = {}

        def insert(item, content_type):
            outcome_id = item.get("outcome_id")
            if not outcome_id:
                return
            if outcome_id not in merged:
                merged[outcome_id] = {
                    "outcome_text": item.get("outcome_text"),
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "teaser": item.get("teaser"),
                    "score": item.get("score"),
                    "matched_terms": item.get("matched_terms", []),
                    "prerequisites": item.get("prerequisites", []),
                    "learning": None,
                    "test": None,
                    "exam": None
                }
            merged[outcome_id][content_type] = {
                "title": item.get("title"),
                "url": item.get("url"),
                "teaser": item.get("teaser")
            }

        for item in learning.values():
            insert(item, "learning")
        for item in test.values():
            insert(item, "test")
        for item in exam.values():
            insert(item, "exam")

        return merged

    # Step 7: Format the display output
    def display_grouped_content(content_dict, label):
        """
        Neatly displays content grouped by outcome.
        Each outcome may include a learning item, a test, and an exam question.
        """
        print(f"\n=== {label.upper()} ===")
        if not content_dict:
            print("No results found.\n")
            return

        for outcome in content_dict.values():
            print(f"Identified syllabus statement / learning outcome: {outcome.get('outcome_text')}")
            print(f"Matched on: {', '.join(outcome['matched_terms'])}")
            print(f"Match score: {outcome['score']} / 1.0")

            if outcome["prerequisites"]:
                print("Prerequisites:")
                for p in outcome["prerequisites"]:
                    print(f"   - {p['title']}")

            # Learning resource
            if outcome["learning"]:
                print(f"\n   Learning resource:")
                print(f"      {outcome['learning']['title']}")
                print(f"      {outcome['learning']['url']}")
                if outcome["learning"].get("teaser"):
                    print(f"      {outcome['learning']['teaser']}")

            # Self test
            if outcome["test"]:
                print(f"\n   Self-test:")
                print(f"      {outcome['test']['title']}")
                print(f"      {outcome['test']['url']}")
                if outcome["test"].get("teaser"):
                    print(f"      {outcome['test']['teaser']}")

            # Exam question
            if outcome["exam"]:
                print(f"\n   Exam question:")
                print(f"      {outcome['exam']['title']}")
                print(f"      {outcome['exam']['url']}")
                if outcome["exam"].get("teaser"):
                    print(f"      {outcome['exam']['teaser']}")

            print()  # spacing

    # Step 8: Merge and display final grouped output
    merged_strong = merge_content_by_outcome(result_learning_strong, result_testing_strong, result_exam_strong)
    merged_related = merge_content_by_outcome(result_learning_related, result_testing_related, result_exam_related)

    display_grouped_content(merged_strong, "Strong Matches")
    display_grouped_content(merged_related, "Related Matches")