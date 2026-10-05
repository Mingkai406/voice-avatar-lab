"""Illustrative retrieval rules and explicit speech events, not a clinical model."""

import re


def retrieval_turn(prompt, previous):
    previous = previous if isinstance(previous, dict) else {}
    stage = int(previous.get("stage", 0)) if str(previous.get("stage", 0)).isdigit() else 0
    stage = max(0, min(3, stage))
    attempts = max(0, min(100, int(previous.get("attempts", 0))))
    low = prompt.lower().strip()
    supplied = bool(re.search(r"\bumbrella\b", low))
    phonemic = bool(
        re.search(r'(?:starts? with|first sound(?: is)?|sound is|say|try)\s*[:"\x27]?\s*(?:um|umb)\b', low)
    ) or low.strip(' .!?"\x27/') in ["um", "umb"]
    semantic = bool(re.search(r"\b(rain|raining|wet|dry)\b|over your head", low))
    encouragement = bool(re.search(r"take your time|no rush|doing well|keep trying|it.s okay", low))
    cue = "none"
    if stage == 3:
        text, reason = "Umbrella. I have it now.", "Retrieved word retained from this session."
        cue = "retained"
    elif supplied:
        text, stage, cue = "Umbrella. Yes, that is the word.", 3, "target"
        reason = "The target word was supplied explicitly."
    elif phonemic:
        text, stage, cue = "Um... umbrella. Yes.", 3, "sound"
        reason = "Relevant sound information supports a new attempt in this example."
    elif semantic:
        text, stage, cue = "For the rain... I know it... the word.", max(1, stage), "meaning"
        reason = "Meaning cue recognized; the word has not yet been retrieved."
    elif re.search(r"starts? with|first sound|first letter", low):
        text, cue = "The sound... which sound?", "incomplete"
        reason = "No matching sound information was supplied; retrieval is unchanged."
    elif encouragement:
        text, cue = "Thank you... give me a moment.", "support"
        reason = "Encouragement acknowledged; it does not supply the missing word."
    else:
        text = "I know it... um... the word." if attempts == 0 else "I... I know it... still trying."
        reason = "Another attempt, with earlier attempts retained in session state."
    state = {
        "stage": stage,
        "attempts": attempts + 1,
        "last_cue": cue,
        "cue_history": (list(previous.get("cue_history", [])) + [cue])[-20:],
    }
    return text, state, reason


def phrase_text(text):
    """Preserve words; repair dense one-word markers into a few phrase boundaries."""
    parts = [p.strip() for p in re.split(r"\.{2,}|…+", text) if p.strip()]
    dense = len(parts) >= 4 and sum(len(p.split()) == 1 for p in parts) >= len(parts) * 0.7
    if len(parts) > 1 and not dense:
        return text
    if dense and any(re.fullmatch(r"(um|uh|erm)[,.!?]?", p, re.I) for p in parts):
        # Keep genuine fillers separate, join adjacent ordinary words into phrases.
        groups = []
        pending = []
        for part in parts:
            if re.fullmatch(r"(um|uh|erm)[,.!?]?", part, re.I):
                if pending:
                    groups.append(" ".join(pending))
                    pending = []
                groups.append(part)
            else:
                pending.append(part)
        if pending:
            groups.append(" ".join(pending))
        return "... ".join(groups)
    plain = " ".join(parts) if dense else text
    # A sparse fallback at a clause/phrase boundary; never insert gaps at every space.
    boundary = re.search(r"\s+(and|but|because)\s+", plain, re.I)
    if boundary and len(plain[: boundary.start()].split()) >= 3:
        return plain[: boundary.start()] + "... " + plain[boundary.start() :].lstrip()
    return plain


def make_plan(text, cue=None):
    """Illustrative phrase timing, not a fitted clinical pause distribution."""
    parts = [p.strip() for p in re.split(r"\.{2,}|…+", text) if p.strip()]
    events = []
    filler = lambda p: bool(re.fullmatch(r"(um|uh|erm)[,.!?]?", p, re.I))
    for i, part in enumerate(parts):
        events.append({"kind": "speech", "text": part, "label": "Speaking"})
        if i == len(parts) - 1:
            continue
        following = parts[i + 1]
        restart = following.lower().startswith(part.lower().rstrip(",.!?") + " ")
        if restart:
            ratio, label = 0.35, "Restart pause"
        elif filler(part):
            ratio, label = 1.5, "Word-finding pause"
        elif filler(following):
            ratio, label = 0.6, "Hesitation pause"
        elif re.match(r"(and|but|because)\b", following, re.I) or re.search(r"[.!?]$", part):
            ratio, label = 0.55, "Phrase pause"
        elif re.search(r"\b(word|remember|called|know it)$", part, re.I):
            ratio, label = 1.65, "Word-finding pause"
        else:
            ratio, label = (1.4 if cue in ["none", "meaning", "incomplete"] else 1.0), "Word-finding pause"
        events.append({"kind": "pause", "scale": ratio, "label": label})
    return events
