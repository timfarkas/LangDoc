## To-Dos
- [ ] bessere anamnese (schemata, vorerkrankungen)
- [ ] logic for rejecting more than one message at a time by user
    - [ ] support for more than one message at a time by user   
- [ ] validation functionality
    - [X] support for parallel processing of many users
    - [ ] case vignette logic  
    - [ ] hallucination statistics
        - [ ] hundred summaries, how many hallucinations?
- [ ] more dynamic summarization, advising and auditing
    - [X] first summary only after four messages
- [X] utilize different gpt models for different sub agents
- [X] fixed typing indicator

### Summary criqitue sys

I will give you a conversation between a doctor and a patient, and then a summary generated by a summary bot. Please tell me, does the conversation match the summary? Think step by step and conclude your reasoning with a ###YES or ###NO.