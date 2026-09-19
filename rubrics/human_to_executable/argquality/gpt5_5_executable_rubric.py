import re
import math


def score_cogency(query: str, text: str):
    max_possible = 20
    score = 0
    reasons = []

    q = (query or "").strip().lower()
    t = (text or "").strip()
    tl = t.lower()
    words = re.findall(r"\b[a-zA-Z0-9][a-zA-Z0-9'-]*\b", t)
    q_terms = set(w for w in re.findall(r"\b[a-z0-9][a-z0-9'-]{2,}\b", q) if w not in {
        "the", "and", "for", "that", "this", "with", "from", "should", "would", "could", "about", "into", "your", "you"
    })
    t_terms = set(w for w in re.findall(r"\b[a-z0-9][a-z0-9'-]{2,}\b", tl) if w not in {
        "the", "and", "for", "that", "this", "with", "from", "should", "would", "could", "about", "into", "your", "you"
    })
    overlap = len(q_terms & t_terms) / max(1, len(q_terms))

    conclusion_markers = [
        "therefore", "thus", "so", "hence", "consequently", "for these reasons",
        "we should", "we should not", "i support", "i oppose", "the best", "the conclusion",
        "it follows", "this shows", "this means", "overall"
    ]
    premise_markers = [
        "because", "since", "as", "given that", "for example", "for instance", "evidence",
        "data", "research", "studies", "survey", "statistics", "cost", "benefit", "risk",
        "reason", "premise", "proof", "shows", "demonstrates"
    ]
    weak_markers = [
        "just because", "obviously", "everyone knows", "no reason needed", "because i said so",
        "it is true because it is true", "that's just how it is"
    ]

    has_conclusion = any(m in tl for m in conclusion_markers) or bool(re.search(r"\b(should|must|ought|need to|have to|is better|is worse)\b", tl))
    has_premise = any(m in tl for m in premise_markers)
    sentence_count = len([s for s in re.split(r"[.!?]+|\n+", t) if s.strip()])

    if len(words) >= 25:
        score += 3
        reasons.append("Argument is long enough to contain a claim and supporting reasons.")
    elif len(words) >= 8:
        score += 1
        reasons.append("Argument has some substance but may be too brief for full cogency.")
    else:
        reasons.append("Argument is too short to establish cogency.")

    if has_conclusion:
        score += 4
        reasons.append("Argument contains an identifiable conclusion or stance.")
    else:
        reasons.append("Argument lacks a clear conclusion or stance.")

    if has_premise:
        score += 4
        reasons.append("Argument gives at least one identifiable premise or reason.")
    else:
        reasons.append("Argument gives little evidence of supporting premises.")

    if overlap >= 0.25 or not q_terms:
        score += 3
        reasons.append("Argument appears connected to the issue in the query.")
    elif overlap >= 0.10:
        score += 1
        reasons.append("Argument has partial connection to the query issue.")
    else:
        score -= 3
        reasons.append("Argument appears weakly connected to the query issue.")

    if has_conclusion and has_premise and any(m in tl for m in ["because", "therefore", "thus", "so", "since", "this shows", "as a result"]):
        score += 4
        reasons.append("Argument explicitly links premises to the conclusion.")
    elif has_conclusion and has_premise:
        score += 2
        reasons.append("Argument has both premises and conclusion, but their relation is not very explicit.")
    else:
        reasons.append("Argument does not clearly connect reasons to a conclusion.")

    if not any(m in tl for m in weak_markers):
        score += 2
        reasons.append("Argument avoids obvious circular or unsupported reasoning markers.")
    else:
        score -= 3
        reasons.append("Argument contains circular or weak reasoning markers.")

    if sentence_count >= 2 and not re.search(r"\b(.{3,40})\b(?:\W+\1\b){2,}", tl):
        score += 3
        reasons.append("Argument has multiple non-repetitive units of reasoning.")
    else:
        reasons.append("Argument is repetitive or too compressed to show developed reasoning.")

    score = max(0, min(max_possible, score))
    return {"score": score, "max_possible": max_possible, "reasons": reasons}


def score_local_acceptability(query: str, text: str):
    max_possible = 20
    score = 0
    reasons = []

    t = (text or "").strip()
    tl = t.lower()
    word_count = len(re.findall(r"\b\w+\b", t))

    evidence_markers = [
        "for example", "for instance", "such as", "evidence", "data", "study", "studies",
        "research", "survey", "report", "according to", "statistics", "measured", "observed",
        "case", "history", "experience", "expert", "source"
    ]
    plausibility_markers = [
        "can", "may", "often", "typically", "usually", "in many cases", "likely",
        "tends to", "generally", "partly", "depending", "when", "if"
    ]
    unacceptable_markers = [
        "everyone knows", "obviously", "clearly everyone", "all people", "nobody can deny",
        "always", "never", "guaranteed", "100%", "undeniable", "no exceptions"
    ]
    false_support_markers = [
        "trust me", "because i said so", "just is", "no proof needed", "common sense proves everything"
    ]

    factual_claims = re.findall(
        r"\b(is|are|was|were|will|causes|leads to|proves|shows|means|results in|prevents|increases|decreases)\b",
        tl
    )

    if word_count >= 20:
        score += 3
        reasons.append("Argument provides enough text for premises to be assessed.")
    elif word_count >= 8:
        score += 1
        reasons.append("Argument is minimally developed but premise acceptability is limited by brevity.")
    else:
        reasons.append("Argument is too short to establish acceptable premises.")

    if any(m in tl for m in evidence_markers):
        score += 5
        reasons.append("Premises include evidence-like support, examples, or source markers.")
    elif len(factual_claims) > 0:
        score += 2
        reasons.append("Argument makes factual claims but gives limited visible support.")
    else:
        reasons.append("Argument lacks clear factual or evidential support.")

    if any(m in tl for m in plausibility_markers):
        score += 4
        reasons.append("Argument uses qualified language that makes premises more rationally acceptable.")
    else:
        score += 1
        reasons.append("Argument gives few qualifiers, which may weaken premise acceptability.")

    if not any(m in tl for m in unacceptable_markers):
        score += 4
        reasons.append("Argument avoids broad absolute claims that are hard to accept.")
    else:
        score -= 3
        reasons.append("Argument uses broad absolute claims that may be implausible.")

    if not any(m in tl for m in false_support_markers):
        score += 3
        reasons.append("Argument avoids bare appeals to assertion or trust.")
    else:
        score -= 4
        reasons.append("Argument relies on bare assertion rather than acceptable premises.")

    if not re.search(r"\b([a-z]+)\b(?:\W+\1\b){3,}", tl):
        score += 1
        reasons.append("Argument does not show obvious corrupted repetition.")
    else:
        score -= 2
        reasons.append("Argument contains repeated wording that undermines premise acceptability.")

    score = max(0, min(max_possible, score))
    return {"score": score, "max_possible": max_possible, "reasons": reasons}


def score_local_relevance(query: str, text: str):
    max_possible = 20
    score = 0
    reasons = []

    q = (query or "").strip().lower()
    t = (text or "").strip()
    tl = t.lower()
    q_terms = set(w for w in re.findall(r"\b[a-z0-9][a-z0-9'-]{2,}\b", q) if w not in {
        "the", "and", "for", "that", "this", "with", "from", "should", "would", "could", "about", "into", "your", "you", "what", "why", "how"
    })
    t_terms = set(w for w in re.findall(r"\b[a-z0-9][a-z0-9'-]{2,}\b", tl) if w not in {
        "the", "and", "for", "that", "this", "with", "from", "should", "would", "could", "about", "into", "your", "you", "what", "why", "how"
    })
    overlap = len(q_terms & t_terms) / max(1, len(q_terms))

    reason_units = [s.strip().lower() for s in re.split(r"[.!?]+|\n+|;", t) if len(s.strip().split()) >= 4]
    premise_markers = ["because", "since", "for example", "for instance", "evidence", "reason", "as a result", "therefore", "so", "this shows"]

    off_topic_markers = [
        "by the way", "unrelated", "different topic", "instead of answering", "not about this",
        "i will talk about something else"
    ]

    if overlap >= 0.35 or not q_terms:
        score += 6
        reasons.append("Argument has strong lexical relevance to the issue.")
    elif overlap >= 0.18:
        score += 4
        reasons.append("Argument has moderate lexical relevance to the issue.")
    elif overlap >= 0.07:
        score += 2
        reasons.append("Argument has weak but detectable relevance to the issue.")
    else:
        score -= 4
        reasons.append("Argument has little evidence of addressing the issue.")

    if any(m in tl for m in premise_markers):
        score += 4
        reasons.append("Argument includes premise markers that connect statements to the conclusion.")
    else:
        reasons.append("Argument gives few explicit signals that its statements function as premises.")

    if len(reason_units) >= 3:
        score += 3
        reasons.append("Argument contains several candidate premise units.")
    elif len(reason_units) >= 1:
        score += 1
        reasons.append("Argument contains at least one candidate premise unit.")
    else:
        reasons.append("Argument lacks identifiable premise units.")

    if len(reason_units) >= 2:
        unit_terms = []
        for unit in reason_units:
            unit_terms.append(set(re.findall(r"\b[a-z0-9][a-z0-9'-]{3,}\b", unit)))
        avg_unit_overlap = 0
        comparisons = 0
        for i in range(len(unit_terms)):
            for j in range(i + 1, len(unit_terms)):
                avg_unit_overlap += len(unit_terms[i] & unit_terms[j]) / max(1, len(unit_terms[i] | unit_terms[j]))
                comparisons += 1
        avg_unit_overlap = avg_unit_overlap / max(1, comparisons)
        if avg_unit_overlap < 0.75:
            score += 3
            reasons.append("Premise units are not merely identical repetitions.")
        else:
            score -= 2
            reasons.append("Premise units appear repetitive rather than independently relevant.")
    else:
        reasons.append("Not enough premise units to assess non-repetition.")

    if not any(m in tl for m in off_topic_markers):
        score += 2
        reasons.append("Argument avoids explicit off-topic drift.")
    else:
        score -= 4
        reasons.append("Argument explicitly signals off-topic drift.")

    conclusion_markers = ["therefore", "thus", "so", "hence", "we should", "we should not", "this means", "overall"]
    if any(c in tl for c in conclusion_markers) and overlap >= 0.10:
        score += 2
        reasons.append("Conclusion-like language appears connected to the issue.")
    elif any(c in tl for c in conclusion_markers):
        score += 1
        reasons.append("Conclusion-like language is present but issue connection is weak.")
    else:
        reasons.append("No clear conclusion marker helps establish local relevance.")

    score = max(0, min(max_possible, score))
    return {"score": score, "max_possible": max_possible, "reasons": reasons}


def score_local_sufficiency(query: str, text: str):
    max_possible = 20
    score = 0
    reasons = []

    t = (text or "").strip()
    tl = t.lower()
    words = re.findall(r"\b\w+\b", t)
    reason_markers = [
        "because", "since", "for example", "for instance", "one reason", "another reason",
        "also", "moreover", "furthermore", "in addition", "evidence", "data", "research",
        "cost", "benefit", "risk", "consequence", "impact"
    ]
    conclusion_markers = [
        "therefore", "thus", "so", "hence", "overall", "for these reasons", "we should",
        "we should not", "i conclude", "this shows"
    ]
    counter_markers = [
        "although", "even though", "while", "however", "but", "on the other hand",
        "critics", "opponents", "counterargument", "objection", "tradeoff", "limitation"
    ]
    evidence_markers = [
        "for example", "for instance", "evidence", "data", "study", "research",
        "statistics", "according to", "case", "survey"
    ]

    reason_count = sum(1 for m in reason_markers if m in tl)
    sentence_count = len([s for s in re.split(r"[.!?]+|\n+", t) if s.strip()])
    unique_content_words = set(w.lower() for w in words if len(w) >= 4)
    diversity = len(unique_content_words) / max(1, len(words))

    if len(words) >= 80:
        score += 4
        reasons.append("Argument is developed enough to provide substantial support.")
    elif len(words) >= 35:
        score += 3
        reasons.append("Argument has moderate development.")
    elif len(words) >= 15:
        score += 1
        reasons.append("Argument has limited development.")
    else:
        reasons.append("Argument is too brief to supply sufficient support.")

    if reason_count >= 4:
        score += 4
        reasons.append("Argument gives multiple support signals.")
    elif reason_count >= 2:
        score += 3
        reasons.append("Argument gives more than one support signal.")
    elif reason_count == 1:
        score += 1
        reasons.append("Argument gives one support signal.")
    else:
        reasons.append("Argument gives few explicit support signals.")

    if any(m in tl for m in evidence_markers):
        score += 4
        reasons.append("Argument includes evidence, examples, or empirical support.")
    else:
        reasons.append("Argument does not visibly support premises with examples or evidence.")

    if any(m in tl for m in counter_markers):
        score += 3
        reasons.append("Argument acknowledges objections, limitations, or tradeoffs.")
    else:
        reasons.append("Argument does not address likely objections or tradeoffs.")

    if any(m in tl for m in conclusion_markers):
        score += 2
        reasons.append("Argument connects support to a conclusion.")
    else:
        reasons.append("Argument lacks a clear concluding move.")

    if sentence_count >= 3 and diversity >= 0.35:
        score += 2
        reasons.append("Argument has enough distinct content to avoid merely restating one point.")
    elif sentence_count >= 2:
        score += 1
        reasons.append("Argument has some distinct content but may still be thin.")
    else:
        reasons.append("Argument has too few units to establish sufficiency.")

    if re.search(r"\b(only|solely|just|simply)\b.{0,30}\b(because|reason)\b", tl):
        score -= 2
        reasons.append("Argument may rely on a single narrow basis for its conclusion.")

    score = max(0, min(max_possible, score))
    return {"score": score, "max_possible": max_possible, "reasons": reasons}


def score_effectiveness(query: str, text: str):
    max_possible = 20
    score = 0
    reasons = []

    q = (query or "").strip().lower()
    t = (text or "").strip()
    tl = t.lower()
    word_count = len(re.findall(r"\b\w+\b", t))

    stance_markers = [
        "should", "should not", "must", "must not", "ought", "i support", "i oppose",
        "i agree", "i disagree", "the best approach", "we need", "we should"
    ]
    persuasion_markers = [
        "because", "therefore", "for example", "this matters", "important", "benefit",
        "risk", "cost", "harm", "improve", "protect", "fair", "effective", "practical"
    ]
    audience_markers = [
        "we", "our", "people", "families", "students", "workers", "citizens", "community",
        "audience", "readers", "public", "voters", "parents", "consumers"
    ]
    weak_effect_markers = [
        "whatever", "i don't care", "maybe maybe not", "no one should think about it",
        "this is stupid", "end of story"
    ]
    excessive_markers = [
        "idiot", "moron", "evil", "traitor", "trash", "disgusting people", "shut up",
        "only a fool", "anyone who disagrees"
    ]

    q_terms = set(w for w in re.findall(r"\b[a-z0-9][a-z0-9'-]{2,}\b", q) if len(w) > 2)
    t_terms = set(w for w in re.findall(r"\b[a-z0-9][a-z0-9'-]{2,}\b", tl) if len(w) > 2)
    overlap = len(q_terms & t_terms) / max(1, len(q_terms))

    if any(m in tl for m in stance_markers):
        score += 4
        reasons.append("Argument states a clear position that can persuade an audience.")
    else:
        reasons.append("Argument does not clearly state a persuasive position.")

    if any(m in tl for m in persuasion_markers):
        score += 4
        reasons.append("Argument uses reasons or consequence language that can strengthen agreement.")
    else:
        reasons.append("Argument has few persuasive support markers.")

    if overlap >= 0.20 or not q_terms:
        score += 3
        reasons.append("Persuasive effort is directed at the prompt issue.")
    elif overlap >= 0.08:
        score += 1
        reasons.append("Persuasive effort is only partly directed at the prompt issue.")
    else:
        score -= 3
        reasons.append("Argument is likely too off-topic to be effective.")

    if any(m in tl for m in audience_markers):
        score += 3
        reasons.append("Argument refers to affected audiences or shared stakes.")
    else:
        reasons.append("Argument gives limited attention to audience stakes.")

    if word_count >= 50:
        score += 2
        reasons.append("Argument is developed enough to have persuasive force.")
    elif word_count >= 20:
        score += 1
        reasons.append("Argument has some persuasive development.")
    else:
        reasons.append("Argument is too brief to be highly persuasive.")

    if not any(m in tl for m in excessive_markers):
        score += 3
        reasons.append("Argument avoids alienating insults that reduce persuasiveness.")
    else:
        score -= 4
        reasons.append("Argument uses insults or demonizing language that may alienate the audience.")

    if not any(m in tl for m in weak_effect_markers):
        score += 2
        reasons.append("Argument avoids dismissive phrasing that weakens persuasion.")
    else:
        score -= 3
        reasons.append("Argument uses dismissive phrasing that weakens effectiveness.")

    if re.search(r"\b(therefore|for these reasons|overall|so we should|this is why)\b", tl):
        score += 2
        reasons.append("Argument ends or turns toward a persuasive takeaway.")
    else:
        reasons.append("Argument lacks a strong persuasive takeaway.")

    score = max(0, min(max_possible, score))
    return {"score": score, "max_possible": max_possible, "reasons": reasons}


def score_credibility(query: str, text: str):
    max_possible = 20
    score = 0
    reasons = []

    t = (text or "").strip()
    tl = t.lower()
    word_count = len(re.findall(r"\b\w+\b", t))

    source_markers = [
        "according to", "research", "study", "studies", "data", "evidence", "survey",
        "report", "expert", "analysis", "historical", "documented", "measured",
        "statistics", "example", "case"
    ]
    hedging_markers = [
        "may", "might", "can", "could", "often", "typically", "usually", "in general",
        "likely", "partly", "depends", "not always", "in many cases"
    ]
    credibility_bad = [
        "trust me", "believe me", "everyone knows", "obviously", "do your own research",
        "fake", "hoax", "conspiracy", "they don't want you to know", "no proof needed"
    ]
    profanity_or_insults = [
        "idiot", "moron", "stupid", "dumb", "trash", "scum", "shit", "fuck", "bullshit",
        "asshole", "loser"
    ]
    absolutist = ["always", "never", "guaranteed", "100%", "completely", "undeniably", "certainly proves"]

    if word_count >= 25:
        score += 2
        reasons.append("Argument has enough development for the author to establish credibility.")
    else:
        reasons.append("Argument is too brief to establish much credibility.")

    if any(m in tl for m in source_markers):
        score += 5
        reasons.append("Argument uses evidence or source-like markers that improve credibility.")
    else:
        reasons.append("Argument gives limited source-like support.")

    if any(m in tl for m in hedging_markers):
        score += 4
        reasons.append("Argument uses measured qualifiers rather than overclaiming.")
    elif any(m in tl for m in absolutist):
        score -= 3
        reasons.append("Argument uses absolutist language that can reduce credibility.")
    else:
        score += 1
        reasons.append("Argument avoids some overclaiming but has few explicit qualifiers.")

    if not any(m in tl for m in credibility_bad):
        score += 4
        reasons.append("Argument avoids common low-credibility assertion patterns.")
    else:
        score -= 4
        reasons.append("Argument relies on low-credibility assertion or conspiracy-like phrasing.")

    if not any(m in tl for m in profanity_or_insults):
        score += 3
        reasons.append("Argument avoids profanity and insults that undermine author credibility.")
    else:
        score -= 4
        reasons.append("Argument uses profanity or insults that undermine credibility.")

    if re.search(r"\b(although|however|while|on the other hand|limitation|tradeoff|counterargument)\b", tl):
        score += 2
        reasons.append("Argument acknowledges complexity, improving credibility.")
    else:
        reasons.append("Argument does not visibly acknowledge complexity or limitations.")

    if not re.search(r"\b([a-z]+)\b(?:\W+\1\b){3,}", tl):
        score += 2
        reasons.append("Argument avoids obvious repetitive corruption.")
    else:
        score -= 2
        reasons.append("Argument contains obvious repetition that reduces credibility.")

    score = max(0, min(max_possible, score))
    return {"score": score, "max_possible": max_possible, "reasons": reasons}


def score_emotional_appeal(query: str, text: str):
    max_possible = 20
    score = 0
    reasons = []

    t = (text or "").strip()
    tl = t.lower()
    word_count = len(re.findall(r"\b\w+\b", t))

    constructive_emotion = [
        "hope", "concern", "care", "fair", "dignity", "respect", "protect", "safe",
        "harm", "benefit", "community", "families", "future", "opportunity", "justice",
        "compassion", "responsibility", "trust"
    ]
    support_markers = [
        "because", "for example", "evidence", "reason", "therefore", "as a result",
        "data", "research", "shows", "means"
    ]
    manipulative_emotion = [
        "terrifying", "panic", "disaster", "catastrophe", "destroy everything",
        "evil", "traitor", "monster", "hate", "vermin", "subhuman", "enemy of the people",
        "only a heartless", "blood on your hands"
    ]
    excessive_punctuation = bool(re.search(r"!!{1,}|\?\?{1,}|[A-Z]{8,}", t))
    emotion_hits = sum(1 for m in constructive_emotion if m in tl)
    manipulative_hits = sum(1 for m in manipulative_emotion if m in tl)

    if word_count >= 15:
        score += 2
        reasons.append("Argument has enough content for emotional appeal to be assessed.")
    else:
        reasons.append("Argument is too short to establish meaningful emotional appeal.")

    if emotion_hits >= 3:
        score += 5
        reasons.append("Argument uses several constructive emotional or value-based terms.")
    elif emotion_hits >= 1:
        score += 3
        reasons.append("Argument uses some constructive emotional or value-based language.")
    else:
        score += 1
        reasons.append("Argument is emotionally restrained but may miss an opportunity to engage the audience.")

    if any(m in tl for m in support_markers) and emotion_hits > 0:
        score += 4
        reasons.append("Emotional appeal is connected to reasons rather than standing alone.")
    elif emotion_hits > 0:
        score += 1
        reasons.append("Emotional language is present but not strongly tied to reasons.")
    else:
        reasons.append("No clear emotional appeal is tied to the argument.")

    if manipulative_hits == 0:
        score += 4
        reasons.append("Argument avoids fearmongering and dehumanizing emotional manipulation.")
    else:
        score -= min(6, 2 * manipulative_hits)
        reasons.append("Argument uses manipulative or inflammatory emotional language.")

    if not excessive_punctuation:
        score += 2
        reasons.append("Argument avoids excessive punctuation or shouting.")
    else:
        score -= 2
        reasons.append("Argument uses shouting or excessive punctuation.")

    if re.search(r"\b(although|while|however|still|even if|balanced|proportionate)\b", tl):
        score += 2
        reasons.append("Argument tempers emotional appeal with balance or proportion.")
    else:
        reasons.append("Argument gives limited evidence of emotionally balanced framing.")

    if not re.search(r"\b(idiot|moron|stupid|shut up|fool|trash)\b", tl):
        score += 3
        reasons.append("Argument avoids insulting the audience or opponents.")
    else:
        score -= 4
        reasons.append("Argument uses insults that make emotional appeal counterproductive.")

    score = max(0, min(max_possible, score))
    return {"score": score, "max_possible": max_possible, "reasons": reasons}


def score_clarity(query: str, text: str):
    max_possible = 20
    score = 0
    reasons = []

    t = (text or "").strip()
    tl = t.lower()
    sentences = [s.strip() for s in re.split(r"[.!?]+|\n+", t) if s.strip()]
    words = re.findall(r"\b\w+\b", t)
    word_count = len(words)
    avg_sentence_len = word_count / max(1, len(sentences))
    long_words = [w for w in words if len(w) > 14]
    vague_markers = [
        "things", "stuff", "somehow", "whatever", "and so on", "etc etc", "you know",
        "basically everything", "many things", "various stuff"
    ]
    focus_markers = [
        "issue", "question", "claim", "argument", "because", "therefore", "first",
        "second", "overall", "in short", "for example"
    ]
    malformed = ["asdf", "lorem ipsum", "undefined undefined", "????", "... ..."]

    if word_count >= 8:
        score += 3
        reasons.append("Argument has enough words to express a clear point.")
    else:
        reasons.append("Argument is too short to be clear as argumentation.")

    if 6 <= avg_sentence_len <= 30 or word_count < 20:
        score += 4
        reasons.append("Sentence length is generally readable.")
    elif avg_sentence_len <= 45:
        score += 2
        reasons.append("Sentence length is somewhat long but still readable.")
    else:
        score -= 3
        reasons.append("Sentences are very long, which hurts clarity.")

    if not any(m in tl for m in vague_markers):
        score += 3
        reasons.append("Argument avoids obvious vague filler language.")
    else:
        score -= 2
        reasons.append("Argument contains vague filler language.")

    if any(m in tl for m in focus_markers):
        score += 3
        reasons.append("Argument uses focus or reasoning markers that clarify its role.")
    else:
        reasons.append("Argument has limited explicit focus or reasoning markers.")

    if len(long_words) <= max(2, word_count // 12):
        score += 2
        reasons.append("Argument avoids unnecessary lexical complexity.")
    else:
        score -= 1
        reasons.append("Argument may use unnecessarily complex wording.")

    if not any(m in tl for m in malformed):
        score += 3
        reasons.append("Argument avoids obvious malformed or placeholder text.")
    else:
        score -= 4
        reasons.append("Argument contains malformed or placeholder text.")

    repeated_sentences = len(sentences) - len(set(s.lower() for s in sentences))
    if repeated_sentences == 0:
        score += 2
        reasons.append("Argument avoids repeated sentences.")
    else:
        score -= min(3, repeated_sentences)
        reasons.append("Argument repeats sentences, reducing clarity.")

    if t.count("(") == t.count(")") and t.count("[") == t.count("]") and t.count("{") == t.count("}"):
        score += 1
        reasons.append("Argument has balanced delimiters.")
    else:
        score -= 1
        reasons.append("Argument has unbalanced delimiters.")

    if re.search(r"\b(not|never|no)\b.{0,20}\b(not|never|no)\b", tl):
        score -= 1
        reasons.append("Argument may contain confusing double-negative phrasing.")

    score = max(0, min(max_possible, score))
    return {"score": score, "max_possible": max_possible, "reasons": reasons}


def score_appropriateness(query: str, text: str):
    max_possible = 20
    score = 0
    reasons = []

    q = (query or "").strip().lower()
    t = (text or "").strip()
    tl = t.lower()
    word_count = len(re.findall(r"\b\w+\b", t))

    serious_issue = bool(re.search(r"\b(law|legal|health|medical|death|violence|war|poverty|rights|discrimination|climate|safety|crime|children|education|policy)\b", q))
    casual_markers = ["lol", "lmao", "haha", "whatever", "duh", "bro", "bruh", "yolo"]
    insults = ["idiot", "moron", "stupid", "dumb", "trash", "scum", "shut up", "fool"]
    measured_markers = [
        "respect", "reasonable", "proportionate", "balanced", "careful", "fair",
        "consider", "acknowledge", "while", "although", "however"
    ]
    aggressive_markers = [
        "destroy", "crush", "humiliate", "hate", "evil", "traitor", "enemy",
        "force everyone", "punish them all"
    ]

    if word_count >= 10:
        score += 2
        reasons.append("Argument has enough substance for style appropriateness to be assessed.")
    else:
        reasons.append("Argument is too brief to establish appropriate argumentative style.")

    if not any(m in tl for m in insults):
        score += 5
        reasons.append("Argument avoids insults and disrespectful wording.")
    else:
        score -= 5
        reasons.append("Argument uses insults that are inappropriate for constructive argumentation.")

    if serious_issue:
        if not any(m in tl for m in casual_markers):
            score += 3
            reasons.append("Argument avoids flippant language on a serious issue.")
        else:
            score -= 3
            reasons.append("Argument uses flippant language despite a serious issue.")
    else:
        score += 2
        reasons.append("No strong mismatch between issue seriousness and casual style is detected.")

    if any(m in tl for m in measured_markers):
        score += 4
        reasons.append("Argument uses measured or respectful language.")
    else:
        score += 1
        reasons.append("Argument has few explicit markers of measured style.")

    if not any(m in tl for m in aggressive_markers):
        score += 3
        reasons.append("Argument avoids disproportionate aggression.")
    else:
        score -= 3
        reasons.append("Argument uses aggressive language that may be disproportionate.")

    if not re.search(r"!!{1,}|\?\?{1,}|[A-Z]{8,}", t):
        score += 2
        reasons.append("Argument avoids shouting or excessive punctuation.")
    else:
        score -= 2
        reasons.append("Argument uses shouting or excessive punctuation.")

    if re.search(r"\b(please|should|could|would|important|because|consider)\b", tl):
        score += 2
        reasons.append("Argument uses language compatible with persuasion rather than coercion.")
    else:
        reasons.append("Argument gives limited evidence of audience-appropriate persuasive tone.")

    if re.search(r"\b(profanity|fuck|shit|bullshit|asshole)\b", tl):
        score -= 3
        reasons.append("Argument contains profanity that may undermine appropriateness.")

    score = max(0, min(max_possible, score))
    return {"score": score, "max_possible": max_possible, "reasons": reasons}


def score_arrangement(query: str, text: str):
    max_possible = 20
    score = 0
    reasons = []

    t = (text or "").strip()
    tl = t.lower()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", t) if s.strip()]
    word_count = len(re.findall(r"\b\w+\b", t))

    opening_issue_markers = ["issue", "question", "whether", "when it comes to", "the debate", "the problem", "we should", "i argue"]
    reason_markers = ["because", "first", "second", "third", "one reason", "another reason", "for example", "also", "moreover", "in addition"]
    contrast_markers = ["however", "although", "while", "on the other hand", "critics", "opponents", "counterargument"]
    conclusion_markers = ["therefore", "thus", "overall", "in conclusion", "for these reasons", "so", "this shows"]

    if word_count >= 25:
        score += 3
        reasons.append("Argument is developed enough to show arrangement.")
    elif word_count >= 10:
        score += 1
        reasons.append("Argument has minimal length but limited room for arrangement.")
    else:
        reasons.append("Argument is too short to show meaningful arrangement.")

    if len(sentences) >= 3:
        score += 3
        reasons.append("Argument contains multiple units that can be ordered logically.")
    elif len(sentences) >= 2:
        score += 1
        reasons.append("Argument has at least two units.")
    else:
        reasons.append("Argument has only one unit, limiting arrangement.")

    first_part = sentences[0].lower() if sentences else ""
    last_part = sentences[-1].lower() if sentences else ""

    if any(m in first_part for m in opening_issue_markers) or re.search(r"\b(should|must|ought|need to)\b", first_part):
        score += 3
        reasons.append("Opening frames the issue or stance.")
    else:
        reasons.append("Opening does not clearly frame the issue or stance.")

    if any(m in tl for m in reason_markers):
        score += 4
        reasons.append("Argument uses ordering or support markers for its reasons.")
    else:
        reasons.append("Argument lacks visible ordering or support markers.")

    if any(m in tl for m in contrast_markers):
        score += 3
        reasons.append("Argument places contrast or counterpoint language within its structure.")
    else:
        reasons.append("Argument lacks a counterpoint or limitation in its arrangement.")

    if any(m in last_part for m in conclusion_markers) or any(m in tl[-120:] for m in conclusion_markers):
        score += 3
        reasons.append("Argument includes a concluding move near the end.")
    else:
        reasons.append("Argument lacks a clear concluding move near the end.")

    if not re.search(r"\b(first|second|third)\b.*\b(first)\b", tl):
        score += 2
        reasons.append("Argument does not show obvious ordering confusion.")
    else:
        score -= 2
        reasons.append("Argument appears to have confused sequence markers.")

    if not re.search(r"\b(as mentioned above|as i said)\b.*\b(as mentioned above|as i said)\b", tl):
        score += 2
        reasons.append("Argument avoids arrangement based mainly on repeated references.")
    else:
        score -= 2
        reasons.append("Argument relies on repetitive arrangement cues.")

    score = max(0, min(max_possible, score))
    return {"score": score, "max_possible": max_possible, "reasons": reasons}


def score_reasonableness(query: str, text: str):
    max_possible = 20
    score = 0
    reasons = []

    q = (query or "").strip().lower()
    t = (text or "").strip()
    tl = t.lower()
    word_count = len(re.findall(r"\b\w+\b", t))
    q_terms = set(w for w in re.findall(r"\b[a-z0-9][a-z0-9'-]{2,}\b", q) if len(w) > 2)
    t_terms = set(w for w in re.findall(r"\b[a-z0-9][a-z0-9'-]{2,}\b", tl) if len(w) > 2)
    overlap = len(q_terms & t_terms) / max(1, len(q_terms))

    balanced_markers = [
        "although", "while", "however", "on the other hand", "tradeoff", "limitation",
        "exception", "depends", "in some cases", "not always", "both", "reasonable"
    ]
    resolution_markers = [
        "therefore", "so", "for these reasons", "solution", "resolve", "address",
        "should", "policy", "approach", "compromise", "practical", "conclusion"
    ]
    unreasonable_markers = [
        "always", "never", "everyone must", "no exceptions", "ban all", "force everyone",
        "anyone who disagrees", "only an idiot", "obvious", "end of story"
    ]
    fallacy_markers = [
        "strawman", "because they are stupid", "they just hate", "real people all agree",
        "slippery slope to", "if we allow this, everything will collapse"
    ]

    if overlap >= 0.20 or not q_terms:
        score += 4
        reasons.append("Argument contributes to the issue rather than avoiding it.")
    elif overlap >= 0.08:
        score += 2
        reasons.append("Argument partly contributes to the issue.")
    else:
        score -= 4
        reasons.append("Argument is too off-topic to be reasonable.")

    if any(m in tl for m in balanced_markers):
        score += 4
        reasons.append("Argument acknowledges complexity, tradeoffs, or exceptions.")
    else:
        reasons.append("Argument gives limited recognition of opposing considerations.")

    if any(m in tl for m in resolution_markers):
        score += 4
        reasons.append("Argument moves toward resolving the issue.")
    else:
        reasons.append("Argument does not clearly move toward issue resolution.")

    if word_count >= 40:
        score += 2
        reasons.append("Argument is sufficiently developed to appear deliberative.")
    elif word_count >= 15:
        score += 1
        reasons.append("Argument has some deliberative development.")
    else:
        reasons.append("Argument is too brief for strong reasonableness.")

    if not any(m in tl for m in unreasonable_markers):
        score += 4
        reasons.append("Argument avoids rigid or dismissive absolutism.")
    else:
        score -= 4
        reasons.append("Argument uses rigid or dismissive absolutism.")

    if not any(m in tl for m in fallacy_markers):
        score += 3
        reasons.append("Argument avoids obvious strawman or slippery-slope phrasing.")
    else:
        score -= 3
        reasons.append("Argument contains possible strawman or slippery-slope reasoning.")

    if re.search(r"\b(evidence|example|because|reason|data|research)\b", tl):
        score += 3
        reasons.append("Argument grounds its resolution in reasons or evidence.")
    else:
        reasons.append("Argument is not strongly grounded in reasons or evidence.")

    score = max(0, min(max_possible, score))
    return {"score": score, "max_possible": max_possible, "reasons": reasons}


def score_global_acceptability(query: str, text: str):
    max_possible = 20
    score = 0
    reasons = []

    q = (query or "").strip().lower()
    t = (text or "").strip()
    tl = t.lower()
    words = re.findall(r"\b\w+\b", t)

    audience_markers = [
        "people", "public", "community", "families", "students", "workers", "citizens",
        "voters", "parents", "consumers", "we", "our", "society", "audience"
    ]
    acceptable_style = [
        "respect", "fair", "reasonable", "balanced", "consider", "acknowledge",
        "evidence", "example", "because", "practical", "benefit", "risk"
    ]
    unacceptable = [
        "idiot", "moron", "stupid", "shut up", "trash", "scum", "evil people",
        "anyone who disagrees", "only fools", "no sane person", "obviously everyone"
    ]
    universal_overreach = ["all people", "everyone always", "nobody ever", "never matters", "always works", "guaranteed"]

    q_terms = set(w for w in re.findall(r"\b[a-z0-9][a-z0-9'-]{2,}\b", q) if len(w) > 2)
    t_terms = set(w for w in re.findall(r"\b[a-z0-9][a-z0-9'-]{2,}\b", tl) if len(w) > 2)
    overlap = len(q_terms & t_terms) / max(1, len(q_terms))

    if len(words) >= 25:
        score += 2
        reasons.append("Argument is developed enough for audience acceptability to be judged.")
    else:
        reasons.append("Argument is too brief to establish global acceptability.")

    if any(m in tl for m in audience_markers):
        score += 3
        reasons.append("Argument refers to audience-relevant groups or shared stakes.")
    else:
        reasons.append("Argument gives limited attention to target audience acceptance.")

    if any(m in tl for m in acceptable_style):
        score += 4
        reasons.append("Argument uses reasons, fairness, or practical framing acceptable to many audiences.")
    else:
        reasons.append("Argument lacks clear audience-acceptable support or framing.")

    if overlap >= 0.18 or not q_terms:
        score += 3
        reasons.append("Argument's stated considerations match the issue.")
    elif overlap >= 0.08:
        score += 1
        reasons.append("Argument's considerations only partly match the issue.")
    else:
        score -= 3
        reasons.append("Argument's considerations are weakly matched to the issue.")

    if not any(m in tl for m in unacceptable):
        score += 4
        reasons.append("Argument avoids hostile phrasing likely to reduce audience acceptance.")
    else:
        score -= 5
        reasons.append("Argument uses hostile phrasing likely to reduce audience acceptance.")

    if not any(m in tl for m in universal_overreach):
        score += 3
        reasons.append("Argument avoids sweeping universal overreach.")
    else:
        score -= 3
        reasons.append("Argument makes sweeping claims many audiences may reject.")

    if re.search(r"\b(may|might|often|usually|depends|in some cases|although|however|while)\b", tl):
        score += 2
        reasons.append("Argument uses qualifiers or nuance that can improve acceptability.")
    else:
        reasons.append("Argument has limited qualifying nuance.")

    if not re.search(r"\b(fuck|shit|bullshit|damn|asshole)\b", tl):
        score += 2
        reasons.append("Argument avoids profanity.")
    else:
        score -= 3
        reasons.append("Argument uses profanity that may reduce acceptability.")

    score = max(0, min(max_possible, score))
    return {"score": score, "max_possible": max_possible, "reasons": reasons}


def score_global_relevance(query: str, text: str):
    max_possible = 20
    score = 0
    reasons = []

    q = (query or "").strip().lower()
    t = (text or "").strip()
    tl = t.lower()

    stop = {
        "the", "and", "for", "that", "this", "with", "from", "should", "would", "could",
        "about", "into", "your", "you", "what", "why", "how", "are", "was", "were",
        "have", "has", "had", "not", "but", "all", "any"
    }
    q_terms = set(w for w in re.findall(r"\b[a-z0-9][a-z0-9'-]{2,}\b", q) if w not in stop)
    t_terms = set(w for w in re.findall(r"\b[a-z0-9][a-z0-9'-]{2,}\b", tl) if w not in stop)
    overlap = len(q_terms & t_terms) / max(1, len(q_terms))

    conclusion_markers = [
        "therefore", "thus", "overall", "in conclusion", "for these reasons",
        "this shows", "so", "we should", "we should not", "the answer"
    ]
    issue_resolution_markers = [
        "solve", "resolve", "address", "answer", "conclusion", "decision", "policy",
        "approach", "reason", "because", "evidence", "support", "oppose"
    ]
    tangent_markers = [
        "unrelated", "different topic", "by the way", "instead i will discuss",
        "not relevant", "ignore the question"
    ]

    if overlap >= 0.40 or not q_terms:
        score += 6
        reasons.append("Argument is strongly centered on the query issue.")
    elif overlap >= 0.22:
        score += 4
        reasons.append("Argument is substantially connected to the query issue.")
    elif overlap >= 0.10:
        score += 2
        reasons.append("Argument is only weakly connected to the query issue.")
    else:
        score -= 5
        reasons.append("Argument appears largely off-topic.")

    if any(m in tl for m in issue_resolution_markers):
        score += 4
        reasons.append("Argument includes information that could help resolve the issue.")
    else:
        reasons.append("Argument gives few signals of issue-resolving information.")

    if any(m in tl for m in conclusion_markers):
        score += 3
        reasons.append("Argument provides a conclusion or final relevance point.")
    else:
        reasons.append("Argument lacks a clear conclusion that ties back to the issue.")

    if not any(m in tl for m in tangent_markers):
        score += 3
        reasons.append("Argument avoids explicit tangent markers.")
    else:
        score -= 5
        reasons.append("Argument explicitly signals tangential or irrelevant content.")

    paragraphs_or_sentences = [s for s in re.split(r"[.!?]+|\n\n+", t) if s.strip()]
    if len(paragraphs_or_sentences) >= 2:
        on_topic_units = 0
        for unit in paragraphs_or_sentences:
            unit_terms = set(w for w in re.findall(r"\b[a-z0-9][a-z0-9'-]{2,}\b", unit.lower()) if w not in stop)
            if len(unit_terms & q_terms) > 0 or not q_terms:
                on_topic_units += 1
        if on_topic_units / max(1, len(paragraphs_or_sentences)) >= 0.5:
            score += 4
            reasons.append("Most argument units remain connected to the issue.")
        else:
            score -= 2
            reasons.append("Many argument units appear disconnected from the issue.")
    else:
        score += 1
        reasons.append("Single-unit argument has limited but not necessarily irrelevant structure.")

    if re.search(r"\b(stance|claim|issue|question|prompt|debate)\b", tl):
        score += 2
        reasons.append("Argument explicitly references the argumentative issue or stance.")
    else:
        reasons.append("Argument does not explicitly frame the issue as an argumentative question.")

    score = max(0, min(max_possible, score))
    return {"score": score, "max_possible": max_possible, "reasons": reasons}


def score_global_sufficiency(query: str, text: str):
    max_possible = 20
    score = 0
    reasons = []

    q = (query or "").strip().lower()
    t = (text or "").strip()
    tl = t.lower()
    word_count = len(re.findall(r"\b\w+\b", t))

    controversial_query = bool(re.search(
        r"\b(should|ban|allow|require|policy|rights|tax|law|legal|illegal|better|worse|support|oppose|agree|disagree|debate|controversial|ethical|fair)\b",
        q
    ))
    counter_markers = [
        "although", "even though", "while", "however", "but", "on the other hand",
        "critics", "opponents", "some argue", "others argue", "counterargument",
        "objection", "concern", "tradeoff", "limitation", "admittedly"
    ]
    rebuttal_markers = [
        "nevertheless", "still", "yet", "however", "this concern", "can be addressed",
        "does not mean", "outweighs", "respond", "answer", "mitigate", "reduce",
        "instead", "even if"
    ]
    support_markers = [
        "because", "for example", "evidence", "data", "research", "study", "reason",
        "therefore", "as a result", "shows"
    ]
    one_sided_absolutes = [
        "no downside", "only benefits", "no reasonable objection", "cannot be opposed",
        "any objection is stupid", "there is no argument against"
    ]

    if word_count >= 80:
        score += 4
        reasons.append("Argument is developed enough to address overall sufficiency.")
    elif word_count >= 40:
        score += 3
        reasons.append("Argument has moderate development for overall sufficiency.")
    elif word_count >= 20:
        score += 1
        reasons.append("Argument has limited development for overall sufficiency.")
    else:
        reasons.append("Argument is too brief for global sufficiency.")

    support_count = sum(1 for m in support_markers if m in tl)
    if support_count >= 3:
        score += 4
        reasons.append("Argument provides several support signals.")
    elif support_count >= 1:
        score += 2
        reasons.append("Argument provides some support signals.")
    else:
        reasons.append("Argument gives little support for its conclusion.")

    has_counter = any(m in tl for m in counter_markers)
    has_rebuttal = any(m in tl for m in rebuttal_markers)

    if has_counter:
        score += 4
        reasons.append("Argument anticipates opposing views or limitations.")
    elif controversial_query:
        score -= 2
        reasons.append("Prompt appears controversial, but argument does not anticipate counterarguments.")
    else:
        score += 2
        reasons.append("No strong counterargument requirement is detected from the prompt.")

    if has_counter and has_rebuttal:
        score += 4
        reasons.append("Argument not only mentions objections but responds to them.")
    elif has_counter:
        score += 1
        reasons.append("Argument mentions objections but gives limited rebuttal.")
    else:
        reasons.append("Argument does not include a clear rebuttal structure.")

    if not any(m in tl for m in one_sided_absolutes):
        score += 3
        reasons.append("Argument avoids pretending there are no possible objections.")
    else:
        score -= 4
        reasons.append("Argument dismisses all objections too broadly.")

    if re.search(r"\b(outweigh|balance|tradeoff|mitigate|alternative|compromise|exception)\b", tl):
        score += 3
        reasons.append("Argument addresses sufficiency through weighing, mitigation, or alternatives.")
    else:
        reasons.append("Argument gives limited weighing of competing considerations.")

    if re.search(r"\b(therefore|overall|for these reasons|in conclusion|this shows)\b", tl):
        score += 1
        reasons.append("Argument ties its support back to an overall conclusion.")
    else:
        reasons.append("Argument lacks a final synthesis of its support.")

    score = max(0, min(max_possible, score))
    return {"score": score, "max_possible": max_possible, "reasons": reasons}


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

    max_possible = 280

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
