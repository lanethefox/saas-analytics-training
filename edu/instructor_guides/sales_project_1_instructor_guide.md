# Instructor Guide: Pipeline Health Assessment Project

## Overview

This guide helps instructors facilitate the Pipeline Health Assessment project, providing guidance on student support, evaluation, and simulated stakeholder interactions.

## Learning Objectives Alignment

Ensure students achieve:
1. **Technical Skills**: SQL proficiency, funnel analysis, cohort analysis
2. **Business Acumen**: Understanding sales processes, identifying bottlenecks
3. **Communication**: Executive-ready presentations, actionable recommendations
4. **Critical Thinking**: Questioning data, considering multiple perspectives

## Project Timeline & Milestones

### Day 1-2: Data Exploration
**Key Activities:**
- Students explore data structure
- Initial queries to understand data quality
- Identify missing or anomalous data

**Instructor Actions:**
- Host kickoff session explaining business context
- Be available for data access questions
- Don't provide answers, guide discovery

**Common Issues:**
- Students may not check data quality first
- Remind them about nulls, duplicates, date ranges
- Encourage exploratory analysis before diving deep

### Day 3-5: Analysis Phase
**Key Activities:**
- Pipeline coverage calculations
- Funnel analysis
- At-risk identification

**Instructor Actions:**
- Review progress in office hours
- Ask probing questions about findings
- Simulate stakeholder questions (see below)

**Guidance Points:**
- Push students beyond basic calculations
- Ask "So what?" to develop business insights
- Encourage multiple analytical approaches

### Day 6: Recommendations
**Key Activities:**
- Synthesizing findings
- Developing action plans
- Quantifying impact

**Instructor Actions:**
- Challenge feasibility of recommendations
- Ask for supporting evidence
- Ensure recommendations are specific

### Day 7: Presentation
**Key Activities:**
- Creating executive deck
- Practicing presentation
- Peer review

**Instructor Actions:**
- Provide presentation feedback
- Simulate executive Q&A
- Focus on business impact

## Stakeholder Simulation Scripts

### Initial Meeting (Day 1)

**You (as VP of Sales):**
"Thanks for taking on this analysis. We're 8 weeks into Q3 and tracking behind. I need to know:
1. Can we still hit our $5M target?
2. Where exactly are we losing deals?
3. What should my team focus on RIGHT NOW?

I don't need perfect - I need actionable by next week. My biggest worry is that we're fooling ourselves with inflated pipeline. Last quarter, 30% of our 'committed' deals pushed to next quarter.

Also, I have a board meeting in 10 days. I need one slide that tells the story. Questions?"

**If student asks about data:**
"Talk to Sales Ops for data access. They have everything in the data warehouse. Focus on the last 6 months for trends, but I care most about THIS quarter."

**If student asks about specific metrics:**
"Good question. Here's what I track daily:
- Pipeline coverage (I want 3.5x minimum)
- Win rate (ours has been dropping)
- Sales cycle (seems to be getting longer)
- Rep attainment (only 8 of 20 reps are on track)"

### Mid-Project Check-in (Day 3-4)

**Email from VP of Sales:**
"Quick update request - the CEO just asked me if we need to adjust guidance. What's your initial read on pipeline health? Can you send me 3 bullets by EOD?

Also, my Enterprise team lead thinks their conversion rates are fine and it's just a coverage issue. The SMB lead says the opposite. What's the data say?

-Sarah"

**Expected Student Response:**
Students should provide:
- Current coverage ratio with confidence level
- Initial bottleneck identification
- Segment-specific insights
- Timeline for full analysis

### Challenging Questions (Day 5-6)

When students present initial findings, challenge them:

**On Pipeline Coverage:**
"You say we have 3.2x coverage, but what's the quality of that pipeline? How much is real vs. happy ears?"

**On Conversion Rates:**
"A 20% win rate sounds low, but is that the real problem? What if we're just not generating enough at the top?"

**On Recommendations:**
"You want reps to focus on stalled deals, but what's the opportunity cost? Should they resurrect dead deals or find new ones?"

**On Forecasting:**
"Your model shows we'll miss by $500K. What's the confidence interval? What assumptions could be wrong?"

### Final Presentation Q&A (Day 7)

Simulate an executive review with these questions:

**Opening:**
"You have 15 minutes. Tell me if we're going to hit the number and what we need to do differently."

**Probing Questions:**
1. "Which of these recommendations will have impact THIS quarter?"
2. "If you could only fix ONE thing, what would it be?"
3. "How do we know this isn't just a seasonal issue?"
4. "What's the #1 risk to your forecast?"
5. "Should I hire more reps or fix the process?"

**Pushback Scenarios:**
- "My top rep says the problem is lead quality, not process. How do you respond?"
- "Finance thinks your forecast is too optimistic. Defend it."
- "The board wants to see improvement in 30 days. What's the quick win?"

## Evaluation Rubric

### Technical Accuracy (30%)
**Excellent (27-30):**
- Complex SQL with CTEs, window functions
- Correct calculations with edge cases handled
- Multiple validation approaches used
- Clean, documented code

**Good (21-26):**
- Accurate basic calculations
- Some advanced SQL usage
- Minor errors that don't affect conclusions
- Readable code

**Needs Improvement (<21):**
- Calculation errors
- Oversimplified analysis
- Missing data quality checks
- Poorly structured queries

### Business Insight (40%)
**Excellent (36-40):**
- Deep understanding of sales process
- Insights go beyond obvious
- Clear cause-and-effect reasoning
- Considers multiple stakeholder perspectives

**Good (28-35):**
- Solid grasp of key issues
- Some non-obvious insights
- Good business reasoning
- Actionable recommendations

**Needs Improvement (<28):**
- Surface-level analysis
- Missing key business implications
- Generic recommendations
- Lack of prioritization

### Communication (20%)
**Excellent (18-20):**
- Executive-ready presentation
- Compelling narrative
- Excellent visualizations
- Handles Q&A confidently

**Good (14-17):**
- Clear presentation
- Good visual aids
- Answers most questions well
- Professional delivery

**Needs Improvement (<14):**
- Unclear messaging
- Poor visual choices
- Struggles with questions
- Too technical for audience

### Completeness (10%)
**Excellent (9-10):**
- All deliverables exceed requirements
- Bonus challenges attempted
- Polished, professional output

**Good (7-8):**
- All deliverables complete
- Meets requirements
- Well-organized

**Needs Improvement (<7):**
- Missing deliverables
- Incomplete analysis
- Disorganized submission

## Common Student Pitfalls & Coaching

### Pitfall 1: Analysis Paralysis
**Symptom:** Student spends too much time perfecting SQL, not enough on insights
**Coaching:** "What decision would this enable? Focus on the 80/20 rule."

### Pitfall 2: Missing the Forest
**Symptom:** Lots of detailed metrics but no clear story
**Coaching:** "If you could only show 3 numbers to the VP, which would they be?"

### Pitfall 3: Unrealistic Recommendations
**Symptom:** Suggests complete process overhaul or unrealistic timelines
**Coaching:** "What could actually be implemented by next week?"

### Pitfall 4: One-Dimensional Analysis
**Symptom:** Only looks at pipeline coverage, ignores quality
**Coaching:** "What other factors might affect whether we hit the target?"

### Pitfall 5: Poor Stakeholder Management
**Symptom:** Too technical, doesn't address business concerns
**Coaching:** "Remember your audience. What keeps the VP up at night?"

## Providing Feedback

### During the Project
- Ask questions rather than giving answers
- Point to resources rather than solving problems
- Encourage peer collaboration
- Use stakeholder persona to guide

### Post-Project Debrief
Structure feedback session:
1. **Self-Assessment** (5 min): What went well? What was challenging?
2. **Peer Feedback** (10 min): Exchange with another student
3. **Instructor Feedback** (10 min): Focus on 2-3 key improvements
4. **Learning Synthesis** (5 min): Key takeaways for next project

### Written Feedback Template
```
Project: Pipeline Health Assessment
Student: [Name]
Grade: [XX/100]

Strengths:
1. [Specific example of excellent work]
2. [Another strength with evidence]

Areas for Improvement:
1. [Specific area with example]
   Suggestion: [Concrete improvement action]
2. [Another area]
   Suggestion: [Concrete improvement action]

Key Learning Points:
- [Important concept they demonstrated understanding of]
- [Skill they developed]

For Next Project:
- [One specific focus area]
- [Resource or strategy to improve]
```

## Additional Resources for Instructors

### Data Scenarios to Introduce
If students finish early or need additional challenge:
1. Add data quality issues (duplicate opportunities)
2. Introduce seasonal patterns
3. Add competitive win/loss data
4. Include economic factors affecting close rates

### Discussion Topics for Class
1. Ethics of pipeline inflation
2. Balancing short-term fixes vs. long-term improvement
3. When to walk away from deals
4. Territory fairness vs. performance

### Real-World Context
Share anonymized examples:
- Actual pipeline review presentations
- Common executive objections
- Success stories from similar analyses
- Industry benchmarks for metrics

## Supporting Struggling Students

### If Student Is Overwhelmed
1. Help them prioritize: "What's the ONE question you must answer?"
2. Provide structured approach: "Let's break this into steps..."
3. Pair with stronger student for specific task
4. Extend deadline if needed with modified scope

### If Student Lacks Business Context
1. Provide additional reading on sales processes
2. Schedule 1:1 to explain sales fundamentals
3. Connect with sales professional for informational interview
4. Use analogies from student's experience

### If Student Struggles with SQL
1. Point to SQL reference guide
2. Provide query templates for common patterns
3. Suggest pair programming session
4. Focus evaluation more on insights than technical execution

## Next Project Connection

Help students see how this project connects to the next (Territory Optimization):
- "The pipeline issues you found - how might better territories help?"
- "You identified rep performance variance - territory design is one factor"
- "Your win rate analysis by segment will inform territory strategy"

This continuity helps students build a comprehensive understanding of sales analytics across projects.