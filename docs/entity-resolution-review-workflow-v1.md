# Entity-resolution review workflow v1

Unresolved procurement suppliers are quarantined from canonical company facts. The queue records the raw name, normalized name, any candidate, method, confidence and why automatic attachment was refused.

A reviewer may approve a mapping only with evidence. Approval creates an alias record containing canonical entity ID, legal/trading/subsidiary alias type, optional parent and registration identifiers, evidence source and approval time. Parent and subsidiary identities remain distinct. Rejection or ambiguity never silently becomes a company mapping.

