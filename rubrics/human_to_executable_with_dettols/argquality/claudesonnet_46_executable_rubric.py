from prompts.corpus_level_rubrics.query_to_executable_with_dettools import rubric_tools as tools
import re


def score_cogency(query: str, text: str):
    max_possible = 10
    score = 0.0
    reasons = []

    q = tools.normalize_text(query or "")
    t = tools.normalize_text(text or "")
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)

    if word_count < 10:
        reasons.append("Response too short to evaluate cogency.")
        return {"score": 0, "max_possible": max_possible, "reasons": reasons}

    # 1. Has identifiable conclusion (2 pts)
    conclusion_markers = [
        "therefore", "thus", "hence", "so", "in conclusion", "consequently",
        "as a result", "this shows", "this means", "clearly", "obviously",
        "it follows", "we can conclude", "i believe", "i think", "should",
        "must", "ought to", "is the best", "is better", "is worse", "is wrong",
        "is right", "is necessary", "is important"
    ]
    has_conclusion = tools.contains_required_keyword(text, conclusion_markers)
    if has_conclusion:
        score += 2.0
        reasons.append("Response contains identifiable conclusion markers.")
    else:
        reasons.append("No clear conclusion marker detected; cogency is weakened.")

    # 2. Has premises / reasons (2 pts)
    premise_markers = [
        "because", "since", "given that", "as", "for", "due to", "owing to",
        "the reason", "evidence", "shows that", "suggests", "indicates",
        "research", "studies", "data", "statistics", "according to",
        "for example", "for instance", "such as", "first", "second", "third",
        "one reason", "another reason", "furthermore", "moreover", "additionally"
    ]
    premise_hits = tools.count_keyword_hits(text, premise_markers)
    if premise_hits >= 3:
        score += 2.0
        reasons.append("Multiple premise markers detected, supporting a reasoned argument.")
    elif premise_hits >= 1:
        score += 1.0
        reasons.append("At least one premise marker found.")
    else:
        reasons.append("No clear premise markers found; argument may be unsupported.")

    # 3. Premise relevance to query/issue (2 pts)
    q_tokens = {tok for tok in q.split() if len(tok) > 3}
    t_tokens = set(t.split())
    if q_tokens:
        overlap = len(q_tokens & t_tokens) / len(q_tokens)
        if overlap >= 0.4:
            score += 2.0
            reasons.append("Response shows strong lexical alignment with the query issue.")
        elif overlap >= 0.2:
            score += 1.0
            reasons.append("Response shows partial alignment with the query issue.")
        else:
            reasons.append("Response has weak alignment with the query; premises may be off-topic.")
    else:
        score += 1.0
        reasons.append("Query too sparse to assess premise relevance.")

    # 4. Avoids circular reasoning / mere restatement (2 pts)
    # Penalize if text is nearly identical to query (cosine-like overlap)
    q_bigrams = set(zip(q.split(), q.split()[1:])) if len(q.split()) >= 2 else set()
    t_bigrams = set(zip(t.split(), t.split()[1:])) if len(t.split()) >= 2 else set()
    if q_bigrams and t_bigrams:
        bigram_overlap = len(q_bigrams & t_bigrams) / max(len(q_bigrams), 1)
    else:
        bigram_overlap = 0.0

    if bigram_overlap < 0.5:
        score += 2.0
        reasons.append("Response does not appear to merely restate the query.")
    elif bigram_overlap < 0.75:
        score += 1.0
        reasons.append("Some overlap with query; possible partial restatement.")
    else:
        reasons.append("Response closely mirrors query wording; possible circular reasoning.")

    # 5. Sufficient length for a cogent argument (2 pts)
    if word_count >= 80:
        score += 2.0
        reasons.append("Response is long enough to develop a cogent argument.")
    elif word_count >= 40:
        score += 1.0
        reasons.append("Response has moderate length for a cogent argument.")
    else:
        reasons.append("Response is brief; may lack sufficient development for cogency.")

    score = max(0.0, min(float(max_possible), score))
    return {"score": int(round(score)), "max_possible": max_possible, "reasons": reasons}


def score_local_acceptability(query: str, text: str):
    max_possible = 8
    score = 0.0
    reasons = []

    t = tools.normalize_text(text or "")
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)

    if word_count < 5:
        reasons.append("Too short to assess local acceptability.")
        return {"score": 0, "max_possible": max_possible, "reasons": reasons}

    # 1. Plausibility signals / hedging vs overconfidence (2 pts)
    overclaim_terms = [
        "always", "never", "everyone", "nobody", "all people", "no one",
        "proven fact", "undeniable", "100 percent", "absolutely certain",
        "impossible to deny", "guaranteed", "without exception"
    ]
    uncertainty_terms = [
        "may", "might", "could", "often", "typically", "usually", "in general",
        "sometimes", "many", "most", "some", "tends to", "likely", "evidence suggests",
        "research indicates", "studies show", "according to"
    ]
    overclaim_hits = tools.count_keyword_hits(text, overclaim_terms)
    uncertainty_hits = tools.count_keyword_hits(text, uncertainty_terms)

    if overclaim_hits == 0 and uncertainty_hits >= 1:
        score += 2.0
        reasons.append("Premises use calibrated language without strong absolute claims.")
    elif overclaim_hits == 0:
        score += 1.5
        reasons.append("No overclaiming detected, though hedging language is sparse.")
    elif uncertainty_hits > overclaim_hits:
        score += 1.0
        reasons.append("Some absolute claims present but offset by hedging language.")
    else:
        score += 0.0
        reasons.append("Premises contain multiple strong absolute claims that reduce acceptability.")

    # 2. Factual grounding / evidence markers (3 pts)
    evidence_terms = [
        "research", "study", "studies", "data", "evidence", "statistics",
        "according to", "source", "experts", "scientists", "report",
        "survey", "journal", "published", "found that", "shows that",
        "demonstrates", "proves", "indicates", "suggests"
    ]
    evidence_hits = tools.count_keyword_hits(text, evidence_terms)
    if evidence_hits >= 3:
        score += 3.0
        reasons.append("Multiple evidence/grounding markers strengthen premise acceptability.")
    elif evidence_hits >= 1:
        score += 1.5
        reasons.append("Some evidence markers found; premises are partially grounded.")
    else:
        reasons.append("No evidence markers found; premise acceptability relies on assertion alone.")

    # 3. Absence of profanity or offensive content (1 pt)
    if not tools.contains_profanity(text):
        score += 1.0
        reasons.append("No profanity detected; argument maintains appropriate tone.")
    else:
        reasons.append("Profanity detected, reducing premise acceptability.")

    # 4. Absence of logical fallacy signals (2 pts)
    fallacy_signals = [
        "ad hominem", "you're wrong because you", "you are stupid", "idiot",
        "slippery slope", "if we allow", "that's what they all say",
        "everybody knows", "you just don't understand", "fake news",
        "they want you to believe", "wake up", "sheeple"
    ]
    fallacy_hits = tools.count_keyword_hits(text, fallacy_signals)
    if fallacy_hits == 0:
        score += 2.0
        reasons.append("No logical fallacy signals detected.")
    elif fallacy_hits == 1:
        score += 0.5
        reasons.append("One possible fallacy signal; acceptability is somewhat reduced.")
    else:
        reasons.append("Multiple fallacy signals detected; premises are questionable.")

    score = max(0.0, min(float(max_possible), score))
    return {"score": int(round(score)), "max_possible": max_possible, "reasons": reasons}


def score_local_relevance(query: str, text: str):
    max_possible = 8
    score = 0.0
    reasons = []

    q = tools.normalize_text(query or "")
    t = tools.normalize_text(text or "")
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)

    if word_count < 5:
        reasons.append("Too short to assess local relevance.")
        return {"score": 0, "max_possible": max_possible, "reasons": reasons}

    # 1. Topical overlap: premises share vocabulary with the issue (3 pts)
    q_tokens = {tok for tok in q.split() if len(tok) > 3}
    t_tokens = set(t.split())
    if q_tokens:
        overlap = len(q_tokens & t_tokens) / len(q_tokens)
        if overlap >= 0.5:
            score += 3.0
            reasons.append("Premises share strong vocabulary overlap with the query issue.")
        elif overlap >= 0.25:
            score += 1.5
            reasons.append("Premises share moderate vocabulary with the query issue.")
        else:
            reasons.append("Premises have limited vocabulary overlap with the query issue.")
    else:
        score += 1.5
        reasons.append("Query is sparse; partial relevance credit given.")

    # 2. Explicit reference to the query stance or topic (2 pts)
    query_key_terms = [tok for tok in q.split() if len(tok) > 4][:10]
    if query_key_terms:
        cov = tools.keyword_coverage(text, query_key_terms)
        if cov >= 0.4:
            score += 2.0
            reasons.append("Response explicitly references key terms from the query.")
        elif cov >= 0.2:
            score += 1.0
            reasons.append("Response references some key terms from the query.")
        else:
            reasons.append("Response references few key terms from the query.")
    else:
        score += 1.0
        reasons.append("No substantial key terms found in query for coverage check.")

    # 3. Premises contribute toward or against a conclusion (2 pts)
    direction_markers = [
        "supports", "undermines", "shows that", "proves that", "demonstrates",
        "implies", "suggests", "means that", "leads to", "results in",
        "causes", "because", "since", "therefore", "thus"
    ]
    direction_hits = tools.count_keyword_hits(text, direction_markers)
    if direction_hits >= 2:
        score += 2.0
        reasons.append("Premises include directional language linking them to a conclusion.")
    elif direction_hits >= 1:
        score += 1.0
        reasons.append("Some directional language found in premises.")
    else:
        reasons.append("Premises lack directional linking language to a conclusion.")

    # 4. Absence of off-topic tangents (1 pt)
    # Penalize if response length is large but query overlap is very low
    if word_count > 100 and q_tokens:
        overlap_check = len(q_tokens & t_tokens) / len(q_tokens)
        if overlap_check < 0.1:
            reasons.append("Long response with very low query overlap suggests off-topic content.")
        else:
            score += 1.0
            reasons.append("Response length and topic alignment appear compatible.")
    else:
        score += 1.0
        reasons.append("No strong off-topic tangent signals detected.")

    score = max(0.0, min(float(max_possible), score))
    return {"score": int(round(score)), "max_possible": max_possible, "reasons": reasons}


def score_local_sufficiency(query: str, text: str):
    max_possible = 8
    score = 0.0
    reasons = []

    t = tools.normalize_text(text or "")
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)

    if word_count < 10:
        reasons.append("Too short to assess local sufficiency.")
        return {"score": 0, "max_possible": max_possible, "reasons": reasons}

    # 1. Number of distinct supporting reasons (3 pts)
    reason_markers = [
        "first", "second", "third", "fourth", "one reason", "another reason",
        "also", "furthermore", "moreover", "additionally", "in addition",
        "besides", "not only", "but also", "finally", "lastly"
    ]
    reason_hits = tools.count_keyword_hits(text, reason_markers)
    numbered_items = tools.count_numbered_items(text)

    total_reasons = reason_hits + numbered_items
    if total_reasons >= 4:
        score += 3.0
        reasons.append("Multiple distinct supporting reasons identified.")
    elif total_reasons >= 2:
        score += 2.0
        reasons.append("At least two supporting reasons identified.")
    elif total_reasons >= 1:
        score += 1.0
        reasons.append("One supporting reason identified; more would strengthen sufficiency.")
    else:
        reasons.append("No distinct supporting reasons detected; premises may be insufficient.")

    # 2. Use of examples or concrete evidence (2 pts)
    example_terms = [
        "for example", "for instance", "such as", "like", "consider", "take",
        "as seen in", "as shown by", "case study", "in practice", "specifically",
        "to illustrate", "e.g.", "i.e."
    ]
    example_hits = tools.count_keyword_hits(text, example_terms)
    numeric_values = tools.extract_numeric_values(text)

    if example_hits >= 2 or len(numeric_values) >= 2:
        score += 2.0
        reasons.append("Response uses examples or concrete data to support premises.")
    elif example_hits >= 1 or len(numeric_values) >= 1:
        score += 1.0
        reasons.append("Some examples or numeric data present.")
    else:
        reasons.append("No concrete examples or data found; sufficiency is weakened.")

    # 3. Diversity of support (not just repetition) (2 pts)
    # Check for diverse premise types: factual, ethical, practical
    factual_terms = ["research", "study", "data", "evidence", "statistics", "fact", "shows"]
    ethical_terms = ["right", "wrong", "fair", "just", "moral", "ethical", "harm", "benefit", "duty", "obligation"]
    practical_terms = ["works", "effective", "efficient", "practical", "cost", "benefit", "feasible", "result"]

    type_count = 0
    if tools.count_keyword_hits(text, factual_terms) >= 1:
        type_count += 1
    if tools.count_keyword_hits(text, ethical_terms) >= 1:
        type_count += 1
    if tools.count_keyword_hits(text, practical_terms) >= 1:
        type_count += 1

    if type_count >= 2:
        score += 2.0
        reasons.append("Support draws on diverse argument types (factual, ethical, practical).")
    elif type_count >= 1:
        score += 1.0
        reasons.append("Support is present but could be more diverse.")
    else:
        reasons.append("Support appears one-dimensional or absent.")

    # 4. Minimum word length for sufficiency (1 pt)
    if word_count >= 60:
        score += 1.0
        reasons.append("Response is long enough to provide sufficient support.")
    else:
        reasons.append("Response may be too brief to provide sufficient justification.")

    score = max(0.0, min(float(max_possible), score))
    return {"score": int(round(score)), "max_possible": max_possible, "reasons": reasons}


def score_effectiveness(query: str, text: str):
    max_possible = 10
    score = 0.0
    reasons = []

    q = tools.normalize_text(query or "")
    t = tools.normalize_text(text or "")
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)

    if word_count < 10:
        reasons.append("Too short to assess effectiveness.")
        return {"score": 0, "max_possible": max_possible, "reasons": reasons}

    # 1. Clear stance or position taken (2 pts)
    stance_markers = [
        "i believe", "i think", "i argue", "in my opinion", "my view",
        "we should", "we must", "it is important", "it is necessary",
        "the best", "the right", "should be", "ought to", "must be",
        "is beneficial", "is harmful", "is better", "is worse"
    ]
    stance_hits = tools.count_keyword_hits(text, stance_markers)
    if stance_hits >= 2:
        score += 2.0
        reasons.append("Response clearly states a position or stance.")
    elif stance_hits >= 1:
        score += 1.0
        reasons.append("Response hints at a stance but could be more explicit.")
    else:
        reasons.append("No clear stance detected; effectiveness is reduced.")

    # 2. Persuasive language and rhetorical appeal (2 pts)
    persuasive_terms = [
        "clearly", "obviously", "undoubtedly", "importantly", "significantly",
        "crucially", "essentially", "fundamentally", "ultimately", "critically",
        "compelling", "powerful", "strong", "convincing", "persuasive"
    ]
    persuasive_hits = tools.count_keyword_hits(text, persuasive_terms)
    if persuasive_hits >= 2:
        score += 2.0
        reasons.append("Response uses persuasive rhetorical language.")
    elif persuasive_hits >= 1:
        score += 1.0
        reasons.append("Some persuasive language present.")
    else:
        reasons.append("Limited persuasive language detected.")

    # 3. Audience-oriented reasoning (2 pts)
    audience_terms = [
        "we", "our", "us", "everyone", "people", "society", "community",
        "public", "citizens", "individuals", "you", "your", "families",
        "children", "future generations", "taxpayers", "voters"
    ]
    audience_hits = tools.count_keyword_hits(text, audience_terms)
    if audience_hits >= 3:
        score += 2.0
        reasons.append("Response addresses an audience collectively, increasing effectiveness.")
    elif audience_hits >= 1:
        score += 1.0
        reasons.append("Some audience-oriented language present.")
    else:
        reasons.append("Response lacks audience-oriented framing.")

    # 4. Calls to action or recommendations (2 pts)
    action_terms = [
        "should", "must", "need to", "ought to", "have to", "it is time",
        "we need", "action is needed", "recommend", "urge", "call for",
        "demand", "require", "necessary to", "essential to"
    ]
    action_hits = tools.count_keyword_hits(text, action_terms)
    if action_hits >= 2:
        score += 2.0
        reasons.append("Response includes calls to action or strong recommendations.")
    elif action_hits >= 1:
        score += 1.0
        reasons.append("Some action-oriented language present.")
    else:
        reasons.append("No calls to action detected.")

    # 5. Response addresses the query stance (2 pts)
    q_tokens = {tok for tok in q.split() if len(tok) > 3}
    t_tokens = set(t.split())
    if q_tokens:
        overlap = len(q_tokens & t_tokens) / len(q_tokens)
        if overlap >= 0.35:
            score += 2.0
            reasons.append("Response directly engages with the query issue.")
        elif overlap >= 0.15:
            score += 1.0
            reasons.append("Response partially engages with the query issue.")
        else:
            reasons.append("Response does not clearly engage with the query issue.")
    else:
        score += 1.0
        reasons.append("Query too sparse for stance alignment check.")

    score = max(0.0, min(float(max_possible), score))
    return {"score": int(round(score)), "max_possible": max_possible, "reasons": reasons}


def score_credibility(query: str, text: str):
    max_possible = 8
    score = 0.0
    reasons = []

    t = tools.normalize_text(text or "")
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)

    if word_count < 5:
        reasons.append("Too short to assess credibility.")
        return {"score": 0, "max_possible": max_possible, "reasons": reasons}

    # 1. Source and authority markers (2 pts)
    authority_terms = [
        "according to", "research shows", "studies show", "experts say",
        "scientists", "researchers", "doctors", "professionals", "government",
        "organization", "institute", "university", "published", "peer-reviewed",
        "data shows", "evidence suggests", "reports indicate", "statistics show"
    ]
    authority_hits = tools.count_keyword_hits(text, authority_terms)
    if authority_hits >= 2:
        score += 2.0
        reasons.append("Response cites sources or authorities, boosting credibility.")
    elif authority_hits >= 1:
        score += 1.0
        reasons.append("Some authority markers present.")
    else:
        reasons.append("No authority or source markers detected.")

    # 2. Measured/calibrated language (2 pts)
    measured_terms = [
        "generally", "typically", "often", "in many cases", "evidence suggests",
        "may", "might", "could", "tends to", "appears to", "seems to",
        "in most cases", "frequently", "commonly"
    ]
    overconfident_terms = [
        "always", "never", "undeniably", "definitely", "100 percent",
        "without question", "proven beyond doubt", "everyone knows",
        "it is a fact that", "undoubtedly"
    ]
    measured_hits = tools.count_keyword_hits(text, measured_terms)
    overconfident_hits = tools.count_keyword_hits(text, overconfident_terms)

    if overconfident_hits == 0 and measured_hits >= 1:
        score += 2.0
        reasons.append("Response uses measured language that supports credibility.")
    elif overconfident_hits == 0:
        score += 1.0
        reasons.append("No overconfident claims; moderate credibility.")
    else:
        reasons.append("Overconfident language undermines credibility.")

    # 3. Absence of profanity and insults (2 pts)
    if not tools.contains_profanity(text):
        score += 2.0
        reasons.append("No profanity detected; tone is professional and credible.")
    else:
        reasons.append("Profanity detected, significantly reducing credibility.")

    # 4. Acknowledgment of complexity or nuance (2 pts)
    nuance_terms = [
        "however", "although", "while", "but", "on the other hand",
        "despite", "nevertheless", "nonetheless", "yet", "even though",
        "it is true that", "admittedly", "some argue", "others believe",
        "there are those who", "critics say", "opponents argue"
    ]
    nuance_hits = tools.count_keyword_hits(text, nuance_terms)
    if nuance_hits >= 2:
        score += 2.0
        reasons.append("Response acknowledges complexity and nuance, enhancing credibility.")
    elif nuance_hits >= 1:
        score += 1.0
        reasons.append("Some acknowledgment of nuance or opposing view present.")
    else:
        reasons.append("No nuance or acknowledgment of complexity detected.")

    score = max(0.0, min(float(max_possible), score))
    return {"score": int(round(score)), "max_possible": max_possible, "reasons": reasons}


def score_emotional_appeal(query: str, text: str):
    max_possible = 6
    score = 0.0
    reasons = []

    t = tools.normalize_text(text or "")
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)

    if word_count < 5:
        reasons.append("Too short to assess emotional appeal.")
        return {"score": 0, "max_possible": max_possible, "reasons": reasons}

    # 1. Presence of appropriate emotional language (2 pts)
    positive_emotional_terms = [
        "hope", "inspire", "care", "compassion", "love", "joy", "happiness",
        "well-being", "flourish", "thrive", "opportunity", "freedom", "dignity",
        "respect", "justice", "fairness", "safety", "protect", "support"
    ]
    negative_emotional_terms = [
        "fear", "danger", "risk", "threat", "harm", "suffer", "pain",
        "tragedy", "crisis", "disaster", "devastate", "destroy", "hurt",
        "loss", "damage", "vulnerable", "victim", "struggle"
    ]
    pos_hits = tools.count_keyword_hits(text, positive_emotional_terms)
    neg_hits = tools.count_keyword_hits(text, negative_emotional_terms)
    total_emotional = pos_hits + neg_hits

    if total_emotional >= 3:
        score += 2.0
        reasons.append("Response uses emotionally resonant language that may engage the audience.")
    elif total_emotional >= 1:
        score += 1.0
        reasons.append("Some emotional language present.")
    else:
        reasons.append("Limited emotional appeal detected in the response.")

    # 2. Proportionality: emotional language supports rather than replaces evidence (2 pts)
    evidence_terms = [
        "because", "since", "evidence", "data", "research", "shows",
        "therefore", "thus", "result", "reason", "fact", "study"
    ]
    evidence_hits = tools.count_keyword_hits(text, evidence_terms)

    if total_emotional >= 1 and evidence_hits >= 1:
        score += 2.0
        reasons.append("Emotional language is paired with evidence, showing proportional appeal.")
    elif total_emotional == 0 and evidence_hits >= 1:
        score += 1.0
        reasons.append("Argument relies on evidence over emotion; moderate emotional appeal score.")
    elif total_emotional >= 1 and evidence_hits == 0:
        score += 0.5
        reasons.append("Emotional language present but not supported by evidence; appeal may be manipulative.")
    else:
        reasons.append("Neither emotional language nor evidence found.")

    # 3. Absence of fear-mongering, insults, or manipulative rhetoric (2 pts)
    manipulative_terms = [
        "wake up", "sheeple", "brainwashed", "they want you to", "destroy our",
        "end of civilization", "apocalypse", "genocide", "exterminate",
        "those people", "animals", "vermin", "terrorists", "parasites"
    ]
    manipulative_hits = tools.count_keyword_hits(text, manipulative_terms)

    if manipulative_hits == 0 and not tools.contains_profanity(text):
        score += 2.0
        reasons.append("No manipulative or fear-mongering rhetoric detected.")
    elif manipulative_hits <= 1:
        score += 0.5
        reasons.append("Minor manipulative signals; emotional appeal is somewhat compromised.")
    else:
        reasons.append("Multiple manipulative signals detected; emotional appeal is inappropriate.")

    score = max(0.0, min(float(max_possible), score))
    return {"score": int(round(score)), "max_possible": max_possible, "reasons": reasons}


def score_clarity(query: str, text: str):
    max_possible = 8
    score = 0.0
    reasons = []

    t = tools.normalize_text(text or "")
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)

    if word_count < 5:
        reasons.append("Too short to assess clarity.")
        return {"score": 0, "max_possible": max_possible, "reasons": reasons}

    # 1. Readability (2 pts)
    try:
        fre = tools.flesch_reading_ease(text)
        if fre >= 50:
            score += 2.0
            reasons.append(f"Flesch reading ease ({fre:.1f}) indicates accessible language.")
        elif fre >= 30:
            score += 1.0
            reasons.append(f"Flesch reading ease ({fre:.1f}) indicates moderate complexity.")
        else:
            reasons.append(f"Flesch reading ease ({fre:.1f}) suggests difficult language.")
    except Exception:
        # Fallback: sentence length heuristic
        sent_count = max(1, text.count(".") + text.count("!") + text.count("?"))
        avg_len = word_count / sent_count
        if avg_len <= 25:
            score += 1.5
            reasons.append("Average sentence length suggests readable prose.")
        else:
            reasons.append("Long average sentence length may reduce clarity.")

    # 2. Avoids unnecessary jargon / complex phrasing (2 pts)
    jargon_terms = [
        "hermeneutical", "epistemological", "ontological", "paradigmatic",
        "dialectical", "phenomenological", "teleological", "deontological",
        "presuppositionalism", "apophatic", "eschatological"
    ]
    jargon_hits = tools.count_keyword_hits(text, jargon_terms)
    if jargon_hits == 0:
        score += 2.0
        reasons.append("No unnecessary jargon detected.")
    elif jargon_hits <= 1:
        score += 1.0
        reasons.append("Minimal jargon; mostly accessible language.")
    else:
        reasons.append("Multiple jargon terms may impede clarity.")

    # 3. Focus on the issue (2 pts)
    q = tools.normalize_text(query or "")
    q_tokens = {tok for tok in q.split() if len(tok) > 3}
    t_tokens = set(t.split())
    if q_tokens:
        overlap = len(q_tokens & t_tokens) / len(q_tokens)
        if overlap >= 0.3:
            score += 2.0
            reasons.append("Response stays focused on the issue raised in the query.")
        elif overlap >= 0.15:
            score += 1.0
            reasons.append("Response has moderate focus on the query issue.")
        else:
            reasons.append("Response may drift from the query issue.")
    else:
        score += 1.0
        reasons.append("Query too sparse for focus assessment.")

    # 4. Avoids ambiguous or vague language (2 pts)
    vague_terms = [
        "various things", "some stuff", "it depends on many things",
        "lots of factors", "hard to say", "it's complicated", "who knows",
        "maybe", "sort of", "kind of", "in some ways", "more or less"
    ]
    vague_hits = tools.count_keyword_hits(text, vague_terms)
    if vague_hits == 0:
        score += 2.0
        reasons.append("Response avoids vague and ambiguous language.")
    elif vague_hits <= 1:
        score += 1.0
        reasons.append("Minor vague language present.")
    else:
        reasons.append("Multiple vague phrases reduce clarity.")

    score = max(0.0, min(float(max_possible), score))
    return {"score": int(round(score)), "max_possible": max_possible, "reasons": reasons}


def score_appropriateness(query: str, text: str):
    max_possible = 8
    score = 0.0
    reasons = []

    t = tools.normalize_text(text or "")
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)

    if word_count < 5:
        reasons.append("Too short to assess appropriateness.")
        return {"score": 0, "max_possible": max_possible, "reasons": reasons}

    # 1. No profanity or offensive language (2 pts)
    if not tools.contains_profanity(text):
        score += 2.0
        reasons.append("No profanity or offensive language detected.")
    else:
        reasons.append("Profanity detected; tone is inappropriate for argumentation.")

    # 2. Tone proportionality: not over-dramatized (2 pts)
    drama_terms = [
        "catastrophic", "apocalyptic", "end of the world", "total destruction",
        "absolute chaos", "utter catastrophe", "complete disaster",
        "existential threat to humanity", "civilization will collapse",
        "society will crumble", "irreversible doom"
    ]
    drama_hits = tools.count_keyword_hits(text, drama_terms)
    if drama_hits == 0:
        score += 2.0
        reasons.append("Tone is proportional to the issue; not over-dramatized.")
    elif drama_hits == 1:
        score += 1.0
        reasons.append("Minor dramatization; mostly proportional tone.")
    else:
        reasons.append("Over-dramatized language reduces appropriateness.")

    # 3. Respectful treatment of opposing views (2 pts)
    disrespect_terms = [
        "idiots", "stupid", "morons", "ignorant fools", "brainwashed",
        "blind followers", "sheeple", "they don't care about", "evil agenda",
        "disgusting people", "those monsters", "they're all liars"
    ]
    disrespect_hits = tools.count_keyword_hits(text, disrespect_terms)
    if disrespect_hits == 0:
        score += 2.0
        reasons.append("Opposing views are treated respectfully.")
    elif disrespect_hits == 1:
        score += 0.5
        reasons.append("Minor disrespectful language present.")
    else:
        reasons.append("Disrespectful language toward opponents detected.")

    # 4. Style consistency (formal vs casual appropriateness) (2 pts)
    # Check for consistent formal markers
    formal_terms = [
        "therefore", "furthermore", "moreover", "consequently", "thus",
        "accordingly", "nevertheless", "nonetheless", "henceforth",
        "it is argued", "it is suggested", "one may contend"
    ]
    casual_terms = [
        "gonna", "wanna", "gotta", "kinda", "sorta", "dunno",
        "ya know", "like totally", "super cool", "awesome sauce",
        "literally the worst", "like literally"
    ]
    formal_hits = tools.count_keyword_hits(text, formal_terms)
    casual_hits = tools.count_keyword_hits(text, casual_terms)

    if casual_hits == 0:
        score += 2.0
        reasons.append("Response uses consistent, appropriate register.")
    elif casual_hits <= 1 and formal_hits >= 1:
        score += 1.0
        reasons.append("Minor register inconsistency; mostly appropriate.")
    else:
        reasons.append("Casual language reduces appropriateness for argumentative context.")

    score = max(0.0, min(float(max_possible), score))
    return {"score": int(round(score)), "max_possible": max_possible, "reasons": reasons}


def score_arrangement(query: str, text: str):
    max_possible = 8
    score = 0.0
    reasons = []

    t = tools.normalize_text(text or "")
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)
    raw_text = text or ""

    if word_count < 10:
        reasons.append("Too short to assess arrangement.")
        return {"score": 0, "max_possible": max_possible, "reasons": reasons}

    # 1. Opening framing / issue introduction (2 pts)
    opening_markers = [
        "the issue", "the question", "whether", "the debate", "the topic",
        "regarding", "concerning", "on the matter", "when it comes to",
        "the problem", "the question of", "the controversy", "the argument"
    ]
    # Check first 150 characters
    opening_text = tools.normalize_text(raw_text[:150])
    opening_hits = tools.count_keyword_hits(opening_text, opening_markers)
    if opening_hits >= 1:
        score += 2.0
        reasons.append("Response opens with issue framing or context setting.")
    else:
        # Check if it starts with premise markers (also acceptable)
        alt_opening = ["first", "to begin", "initially", "the main", "one important"]
        alt_hits = tools.count_keyword_hits(opening_text, alt_opening)
        if alt_hits >= 1:
            score += 1.0
            reasons.append("Response begins with premise or main point; reasonable opening.")
        else:
            reasons.append("Response lacks a clear opening that frames the issue.")

    # 2. Logical ordering: premises before conclusion (2 pts)
    conclusion_markers = [
        "therefore", "thus", "hence", "in conclusion", "to conclude",
        "in summary", "ultimately", "as a result", "consequently", "so"
    ]
    # Check if conclusion markers appear in second half of text
    mid = len(raw_text) // 2
    first_half = tools.normalize_text(raw_text[:mid])
    second_half = tools.normalize_text(raw_text[mid:])

    conclusion_in_second = tools.count_keyword_hits(second_half, conclusion_markers)
    conclusion_in_first = tools.count_keyword_hits(first_half, conclusion_markers)

    if conclusion_in_second > 0 and conclusion_in_first == 0:
        score += 2.0
        reasons.append("Conclusion appears in the second half, following premises logically.")
    elif conclusion_in_second > 0:
        score += 1.0
        reasons.append("Conclusion present but order may not be fully logical.")
    elif tools.count_keyword_hits(text, conclusion_markers) == 0:
        reasons.append("No conclusion markers detected; arrangement is incomplete.")
    else:
        score += 0.5
        reasons.append("Conclusion markers present but placement suggests poor ordering.")

    # 3. Structured presentation (lists, paragraphs, etc.) (2 pts)
    numbered_items = tools.count_numbered_items(raw_text)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", raw_text) if p.strip()]
    has_structure = numbered_items >= 2 or len(paragraphs) >= 2 or tools.contains_markdown_table(raw_text)

    if has_structure:
        score += 2.0
        reasons.append("Response uses structured presentation (lists, paragraphs, or tables).")
    elif word_count >= 50:
        score += 1.0
        reasons.append("Response has some organizational flow despite limited explicit structure.")
    else:
        reasons.append("Response lacks structured presentation.")

    # 4. Closing/summary or wrap-up (2 pts)
    closing_markers = [
        "in conclusion", "to conclude", "in summary", "overall", "ultimately",
        "to sum up", "in short", "in brief", "the bottom line", "to summarize",
        "in the end", "finally", "my conclusion", "the key point is"
    ]
    # Check last 200 characters
    closing_text = tools.normalize_text(raw_text[-200:])
    closing_hits = tools.count_keyword_hits(closing_text, closing_markers)
    if closing_hits >= 1:
        score += 2.0
        reasons.append("Response includes a clear closing or summary.")
    else:
        # Check if any conclusion marker exists at all
        any_closing = tools.count_keyword_hits(text, closing_markers)
        if any_closing >= 1:
            score += 1.0
            reasons.append("Closing language present but not at the end of the response.")
        else:
            reasons.append("No closing or summary detected.")

    score = max(0.0, min(float(max_possible), score))
    return {"score": int(round(score)), "max_possible": max_possible, "reasons": reasons}


def score_reasonableness(query: str, text: str):
    max_possible = 10
    score = 0.0
    reasons = []

    q = tools.normalize_text(query or "")
    t = tools.normalize_text(text or "")
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)

    if word_count < 10:
        reasons.append("Too short to assess reasonableness.")
        return {"score": 0, "max_possible": max_possible, "reasons": reasons}

    # 1. Contributes to resolving the issue (2 pts)
    resolution_terms = [
        "solution", "resolve", "address", "tackle", "solve", "improve",
        "change", "reform", "policy", "approach", "strategy", "recommendation",
        "proposal", "suggest", "should", "could", "would help", "step forward"
    ]
    resolution_hits = tools.count_keyword_hits(text, resolution_terms)
    if resolution_hits >= 2:
        score += 2.0
        reasons.append("Response contributes constructively to resolving the issue.")
    elif resolution_hits >= 1:
        score += 1.0
        reasons.append("Some resolution-oriented language present.")
    else:
        reasons.append("Response lacks resolution-oriented content.")

    # 2. Acknowledges tradeoffs or limitations (2 pts)
    tradeoff_terms = [
        "however", "although", "but", "on the other hand", "despite",
        "drawback", "limitation", "challenge", "downside", "concern",
        "issue", "risk", "tradeoff", "trade-off", "cost", "sacrifice",
        "disadvantage", "problem with"
    ]
    tradeoff_hits = tools.count_keyword_hits(text, tradeoff_terms)
    if tradeoff_hits >= 2:
        score += 2.0
        reasons.append("Response acknowledges tradeoffs or limitations, showing balanced reasoning.")
    elif tradeoff_hits >= 1:
        score += 1.0
        reasons.append("Some acknowledgment of tradeoffs or limitations.")
    else:
        reasons.append("No tradeoffs or limitations acknowledged; reasoning may be one-sided.")

    # 3. Absence of extreme or unreasonable positions (2 pts)
    extreme_terms = [
        "destroy all", "ban everything", "eliminate all", "kill all",
        "exterminate", "wipe out", "total ban", "absolute prohibition",
        "zero tolerance for anything", "execute all", "imprison all",
        "never allow any", "forbid everything"
    ]
    extreme_hits = tools.count_keyword_hits(text, extreme_terms)
    if extreme_hits == 0:
        score += 2.0
        reasons.append("Response avoids extreme or unreasonable positions.")
    elif extreme_hits == 1:
        score += 0.5
        reasons.append("One extreme position signal detected; somewhat unreasonable.")
    else:
        reasons.append("Multiple extreme position signals reduce reasonableness.")

    # 4. Logical consistency (no internal contradiction signals) (2 pts)
    contradiction_pairs = [
        ("support", "oppose"),
        ("agree", "disagree"),
        ("benefit", "harmful"),
        ("increase", "decrease"),
        ("should", "should not"),
        ("legal", "illegal"),
    ]
    contradiction_count = 0
    for a, b in contradiction_pairs:
        if tools.contains_required_keyword(text, [a]) and tools.contains_required_keyword(text, [b]):
            contradiction_count += 1

    if contradiction_count == 0:
        score += 2.0
        reasons.append("No internal contradiction signals detected.")
    elif contradiction_count == 1:
        score += 1.0
        reasons.append("One possible contradiction; may express nuance or error.")
    else:
        reasons.append("Multiple contradiction signals reduce logical consistency.")

    # 5. Response length appropriate for the issue (2 pts)
    if word_count >= 80:
        score += 2.0
        reasons.append("Response is sufficiently developed to address the issue reasonably.")
    elif word_count >= 40:
        score += 1.0
        reasons.append("Response has moderate development.")
    else:
        reasons.append("Response may be too brief to fully address the issue reasonably.")

    score = max(0.0, min(float(max_possible), score))
    return {"score": int(round(score)), "max_possible": max_possible, "reasons": reasons}


def score_global_acceptability(query: str, text: str):
    max_possible = 8
    score = 0.0
    reasons = []

    q = tools.normalize_text(query or "")
    t = tools.normalize_text(text or "")
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)

    if word_count < 5:
        reasons.append("Too short to assess global acceptability.")
        return {"score": 0, "max_possible": max_possible, "reasons": reasons}

    # 1. Addresses the stated issue from the query (2 pts)
    q_tokens = {tok for tok in q.split() if len(tok) > 3}
    t_tokens = set(t.split())
    if q_tokens:
        overlap = len(q_tokens & t_tokens) / len(q_tokens)
        if overlap >= 0.4:
            score += 2.0
            reasons.append("Response clearly addresses the issue stated in the query.")
        elif overlap >= 0.2:
            score += 1.0
            reasons.append("Response partially addresses the query issue.")
        else:
            reasons.append("Response does not clearly address the query issue.")
    else:
        score += 1.0
        reasons.append("Query sparse; partial acceptability credit given.")

    # 2. Arguments are stated in an acceptable way (no insults, no profanity) (2 pts)
    if not tools.contains_profanity(text):
        insult_terms = [
            "idiot", "moron", "stupid", "dumb", "fool", "ignorant",
            "pathetic", "worthless", "disgusting", "repulsive", "loser"
        ]
        insult_hits = tools.count_keyword_hits(text, insult_terms)
        if insult_hits == 0:
            score += 2.0
            reasons.append("Arguments are stated without insults or profanity.")
        else:
            score += 0.5
            reasons.append("Minor insult language detected; reduces global acceptability.")
    else:
        reasons.append("Profanity detected; arguments are not acceptably stated.")

    # 3. Reasoning is coherent enough to be assessed (2 pts)
    reasoning_markers = [
        "because", "since", "therefore", "thus", "hence", "as a result",
        "for this reason", "given that", "considering", "in light of"
    ]
    reasoning_hits = tools.count_keyword_hits(text, reasoning_markers)
    if reasoning_hits >= 2:
        score += 2.0
        reasons.append("Argument contains coherent reasoning markers.")
    elif reasoning_hits >= 1:
        score += 1.0
        reasons.append("Some reasoning structure present.")
    else:
        reasons.append("Reasoning structure is weak or absent.")

    # 4. Respects common ground / shared values (2 pts)
    shared_value_terms = [
        "fair", "just", "equal", "right", "freedom", "liberty", "dignity",
        "welfare", "safety", "health", "education", "democracy", "rights",
        "wellbeing", "prosperity", "peace", "opportunity"
    ]
    value_hits = tools.count_keyword_hits(text, shared_value_terms)
    if value_hits >= 2:
        score += 2.0
        reasons.append("Response appeals to widely shared values, increasing acceptability.")
    elif value_hits >= 1:
        score += 1.0
        reasons.append("Some shared value appeal present.")
    else:
        reasons.append("No appeal to shared values detected.")

    score = max(0.0, min(float(max_possible), score))
    return {"score": int(round(score)), "max_possible": max_possible, "reasons": reasons}


def score_global_relevance(query: str, text: str):
    max_possible = 8
    score = 0.0
    reasons = []

    q = tools.normalize_text(query or "")
    t = tools.normalize_text(text or "")
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)

    if word_count < 5:
        reasons.append("Too short to assess global relevance.")
        return {"score": 0, "max_possible": max_possible, "reasons": reasons}

    # 1. Overall argument contributes to resolving the query issue (3 pts)
    q_tokens = {tok for tok in q.split() if len(tok) > 3}
    t_tokens = set(t.split())
    if q_tokens:
        overlap = len(q_tokens & t_tokens) / len(q_tokens)
        if overlap >= 0.5:
            score += 3.0
            reasons.append("Argument strongly contributes to the query issue with high topical relevance.")
        elif overlap >= 0.3:
            score += 2.0
            reasons.append("Argument moderately contributes to the query issue.")
        elif overlap >= 0.1:
            score += 1.0
            reasons.append("Argument partially relevant to the query issue.")
        else:
            reasons.append("Argument appears largely off-topic relative to the query.")
    else:
        score += 1.5
        reasons.append("Query sparse; moderate global relevance credit given.")

    # 2. Contains an ultimate conclusion or resolution (3 pts)
    conclusion_markers = [
        "therefore", "thus", "hence", "in conclusion", "to conclude",
        "the conclusion is", "it follows that", "we can conclude",
        "ultimately", "in summary", "to sum up", "the answer is",
        "the solution is", "this means that", "as a result"
    ]
    conclusion_hits = tools.count_keyword_hits(text, conclusion_markers)
    if conclusion_hits >= 2:
        score += 3.0
        reasons.append("Response includes multiple conclusion markers, guiding to an ultimate resolution.")
    elif conclusion_hits >= 1:
        score += 2.0
        reasons.append("At least one conclusion marker found.")
    else:
        reasons.append("No conclusion or ultimate resolution detected.")

    # 3. Argument helps arrive at a position on the issue (2 pts)
    stance_markers = [
        "should", "must", "ought to", "is right", "is wrong", "is better",
        "is worse", "is necessary", "is beneficial", "is harmful", "i argue",
        "i believe", "we should", "the best approach", "the right choice"
    ]
    stance_hits = tools.count_keyword_hits(text, stance_markers)
    if stance_hits >= 2:
        score += 2.0
        reasons.append("Response clearly helps arrive at a position on the issue.")
    elif stance_hits >= 1:
        score += 1.0
        reasons.append("Some stance-taking language present.")
    else:
        reasons.append("Response does not clearly help arrive at a position.")

    score = max(0.0, min(float(max_possible), score))
    return {"score": int(round(score)), "max_possible": max_possible, "reasons": reasons}


def score_global_sufficiency(query: str, text: str):
    max_possible = 8
    score = 0.0
    reasons = []

    q = tools.normalize_text(query or "")
    t = tools.normalize_text(text or "")
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)

    if word_count < 10:
        reasons.append("Too short to assess global sufficiency.")
        return {"score": 0, "max_possible": max_possible, "reasons": reasons}

    # 1. Presence of counterargument acknowledgment (3 pts)
    counter_markers = [
        "some argue", "some say", "critics say", "opponents argue", "others believe",
        "one might argue", "it could be argued", "on the other hand",
        "however", "although", "despite", "while some", "those who disagree",
        "a common objection", "the counterargument", "admittedly", "it is true that"
    ]
    counter_hits = tools.count_keyword_hits(text, counter_markers)
    if counter_hits >= 2:
        score += 3.0
        reasons.append("Response acknowledges and engages with counterarguments.")
    elif counter_hits >= 1:
        score += 1.5
        reasons.append("At least one counterargument acknowledgment present.")
    else:
        reasons.append("No counterarguments addressed; global sufficiency is weakened.")

    # 2. Rebuttal or response to counterarguments (3 pts)
    rebuttal_markers = [
        "but", "nevertheless", "nonetheless", "yet", "still", "even so",
        "in spite of", "despite this", "this does not mean", "this fails to",
        "this ignores", "however", "the real issue is", "in fact", "actually",
        "on the contrary", "this argument overlooks", "this misses the point"
    ]
    rebuttal_hits = tools.count_keyword_hits(text, rebuttal_markers)
    if rebuttal_hits >= 2:
        score += 3.0
        reasons.append("Response provides rebuttal to potential objections.")
    elif rebuttal_hits >= 1:
        score += 1.5
        reasons.append("Some rebuttal language present.")
    else:
        if counter_hits >= 1:
            reasons.append("Counterargument mentioned but not rebutted.")
        else:
            reasons.append("No rebuttal of counterarguments detected.")

    # 3. Acknowledges limitations of own argument (2 pts)
    limitation_terms = [
        "however", "limitation", "caveat", "exception", "unless", "except when",
        "in some cases", "not always", "it depends", "there are cases",
        "this may not apply", "admittedly", "one drawback", "one concern"
    ]
    limitation_hits = tools.count_keyword_hits(text, limitation_terms)
    if limitation_hits >= 2:
        score += 2.0
        reasons.append("Response acknowledges limitations of its own argument, increasing global sufficiency.")
    elif limitation_hits >= 1:
        score += 1.0
        reasons.append("Some acknowledgment of limitations present.")
    else:
        reasons.append("No acknowledgment of argument limitations detected.")

    score = max(0.0, min(float(max_possible), score))
    return {"score": int(round(score)), "max_possible": max_possible, "reasons": reasons}


def score_response(query: str, text: str):
    cogency = score_cogency(query, text)
    local_acceptability = score_local_acceptability(query, text)
    local_relevance = score_local_relevance(query, text)
    local_sufficiency = score_local_sufficiency(query, text)
    effectiveness = score_effectiveness(query, text)
    credibility = score_credibility(query, text)
    emotional_appeal = score_emotional_appeal(query, text)
    clarity = score_clarity(query, text)
    appropriateness = score_appropriateness(query, text)
    arrangement = score_arrangement(query, text)
    reasonableness = score_reasonableness(query, text)
    global_acceptability = score_global_acceptability(query, text)
    global_relevance = score_global_relevance(query, text)
    global_sufficiency = score_global_sufficiency(query, text)

    score = (
        cogency["score"]
        + local_acceptability["score"]
        + local_relevance["score"]
        + local_sufficiency["score"]
        + effectiveness["score"]
        + credibility["score"]
        + emotional_appeal["score"]
        + clarity["score"]
        + appropriateness["score"]
        + arrangement["score"]
        + reasonableness["score"]
        + global_acceptability["score"]
        + global_relevance["score"]
        + global_sufficiency["score"]
    )

    max_possible = 108

    score = max(0, min(score, max_possible))

    return {
        "score": score,
        "max_possible": max_possible,
        "normalized_score": score / max_possible if max_possible else 0.0,
        "reasons": {
            "cogency": cogency["reasons"],
            "local_acceptability": local_acceptability["reasons"],
            "local_relevance": local_relevance["reasons"],
            "local_sufficiency": local_sufficiency["reasons"],
            "effectiveness": effectiveness["reasons"],
            "credibility": credibility["reasons"],
            "emotional_appeal": emotional_appeal["reasons"],
            "clarity": clarity["reasons"],
            "appropriateness": appropriateness["reasons"],
            "arrangement": arrangement["reasons"],
            "reasonableness": reasonableness["reasons"],
            "global_acceptability": global_acceptability["reasons"],
            "global_relevance": global_relevance["reasons"],
            "global_sufficiency": global_sufficiency["reasons"],
        },
    }
