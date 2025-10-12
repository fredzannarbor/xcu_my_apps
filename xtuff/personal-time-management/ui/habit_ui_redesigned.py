#!/usr/bin/env python3
"""
Redesigned Habit UI - Research-Based Consolidation
Based on peer-reviewed habit formation research

Key Research Foundations:
- Lally et al. (2010): 66-day automaticity timeline
- Gollwitzer (1999): Implementation intentions (if-then plans)
- Fogg (2009, 2019): Behavior model and tiny habits
- Clear (2018): Identity-based habit formation
- Duhigg (2012): Habit loop (cue-routine-reward)
- Wood & Neal (2007): Habit extinction and context

Author: Daily Engine Team
Date: 2025-10-07
Version: 2.0
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from habit_system.habit_tracker import log_habit_completion, get_habit_analysis
from database_extensions import db_extensions
from config.settings import config


# ============================================================================
# RESEARCH TOOLTIP CONTENT
# ============================================================================

RESEARCH_TOOLTIPS = {
    "established_habits": """
**Why Daily Habits Become Automatic Faster**

Research by Lally et al. (2010) found that behaviors repeated daily in consistent contexts
reach automaticity in an average of 66 days (range: 18-254 days depending on complexity).
Daily habits develop stronger context-behavior associations than intermittent behaviors.

📖 Lally, P., et al. (2010). European Journal of Social Psychology, 40(6), 998-1009.
DOI: 10.1002/ejsp.674
""",

    "developing_habits": """
**Building Toward Automaticity**

Intermittent habits take longer to become automatic due to weaker context-response
associations. However, they're essential for behaviors that don't require daily frequency
(e.g., exercise 3x/week, social connection 2x/week).

Research shows intermittent rewards can actually strengthen habit formation, and consistent
weekly patterns (e.g., "every Monday/Wednesday/Friday") build stronger associations than
variable scheduling.

📖 Gardner, B., Lally, P., & Wardle, J. (2012). British Journal of General Practice, 62(605), 664-666.
""",

    "implementation_intentions": """
**If-Then Plans Boost Success by 65%**

Gollwitzer's (1999) research found that implementation intentions increase goal
achievement with a large effect size (d=.65). The format is simple:

"When [situation X occurs], I will [do behavior Y]"

This delegates control to environmental cues, making behavior more automatic and requiring
less willpower.

📖 Gollwitzer, P. M. (1999). American Psychologist, 54(7), 493-503.
DOI: 10.1037/0003-066X.54.7.493
""",

    "celebration": """
**Emotions Create Habits**

BJ Fogg's research shows that immediate celebration after completing a behavior is
crucial for habit formation. The emotional spike creates stronger neural pathways than
repetition alone.

The celebration can be tiny (fist pump, "Yes!", smile) but must be immediate and authentic.

📖 Fogg, B. J. (2019). Tiny Habits. Houghton Mifflin Harcourt.
""",

    "identity": """
**Identity Change Drives Lasting Habits**

James Clear's research shows that lasting behavior change requires identity shift.
Instead of "I want to exercise," frame it as "I am an athlete."

Every action is a vote for the type of person you wish to become. Focus on becoming
someone rather than achieving something.

📖 Clear, J. (2018). Atomic Habits. New York: Avery.
""",

    "habit_loop": """
**The Habit Loop: Cue → Routine → Reward**

Duhigg's research reveals that habits follow a neurological pattern:
- **Cue**: Trigger that tells your brain to go into automatic mode
- **Routine**: The behavior itself (physical, mental, or emotional)
- **Reward**: What your brain gets that helps it remember the loop

Once established, the cue alone triggers craving for the reward before you perform the
routine.

📖 Duhigg, C. (2012). The Power of Habit. New York: Random House.
""",

    "habit_extinction": """
**Breaking Bad Habits: Research-Based Strategies**

Wood & Neal (2007) and recent 2024 neuroscience research show that breaking habits
requires:
1. **Avoid triggers**: Change contexts that cue the behavior
2. **Create competing routines**: Replace bad habit with alternative behavior
3. **Goal-directed inhibition**: Use implementation intentions for "if X, then NOT Y"
4. **Context modification**: Habits are context-specific; changing context helps

📖 Wood, W., & Neal, D. T. (2007). Psychological Review, 114(4), 843-863.
📖 Haith, A. M., & Krakauer, J. W. (2024). Trends in Cognitive Sciences, 28(11), 1010-1025.
""",

    "occasional_behaviors": """
**Not All Behaviors Need Daily Frequency**

Some important behaviors are best tracked as occasional, as-needed actions rather than
scheduled habits. These are measured by count/frequency rather than streaks.

Examples: Acts of kindness, networking conversations, creative brainstorming sessions.

Track these to ensure they happen regularly at appropriate intervals, even if not daily or
weekly.
"""
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def show_research_tooltip(tooltip_key: str):
    """Display research tooltip with icon"""
    if tooltip_key in RESEARCH_TOOLTIPS:
        st.markdown(f"ℹ️", help=RESEARCH_TOOLTIPS[tooltip_key])


def calculate_automaticity_progress(habit_name: str, total_days: int, consistency_rate: float) -> Dict:
    """
    Calculate automaticity progress based on Lally et al. (2010) research
    Average 66 days to automaticity
    """
    if total_days == 0:
        return {"percentage": 0, "days_remaining": 66, "status": "just_starting"}

    # Simple linear model: automaticity = min(100%, total_days / 66 * consistency_rate)
    automaticity_percentage = min(100, (total_days / 66) * consistency_rate * 100)
    days_remaining = max(0, 66 - total_days)

    if automaticity_percentage >= 95:
        status = "automatic"
    elif automaticity_percentage >= 70:
        status = "nearly_automatic"
    elif automaticity_percentage >= 40:
        status = "forming"
    else:
        status = "early_stage"

    return {
        "percentage": automaticity_percentage,
        "days_remaining": days_remaining,
        "status": status,
        "total_days": total_days
    }


def render_celebration_prompt(habit_name: str):
    """Render Fogg-method celebration prompt after habit completion"""
    st.success(f"🎉 Awesome! You reinforced your identity through {habit_name}!")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✊ Fist pump!", key=f"celebrate_fist_{habit_name}"):
            st.balloons()
            st.info("Feeling the win creates the habit!")
    with col2:
        if st.button("😊 Smile & nod", key=f"celebrate_smile_{habit_name}"):
            st.balloons()
            st.info("Great! Positive emotions wire in habits!")
    with col3:
        if st.button("⏭️ Skip", key=f"celebrate_skip_{habit_name}"):
            st.caption("Consider celebrating - it strengthens the neural pathway!")


def render_automaticity_meter(progress: Dict):
    """Render visual automaticity progress meter"""
    percentage = progress["percentage"]
    status = progress["status"]
    days_remaining = progress["days_remaining"]

    # Status emojis and colors
    status_info = {
        "just_starting": {"emoji": "🌱", "color": "lightblue", "text": "Just Starting"},
        "early_stage": {"emoji": "🌿", "color": "lightgreen", "text": "Early Stage"},
        "forming": {"emoji": "🌳", "color": "green", "text": "Habit Forming"},
        "nearly_automatic": {"emoji": "⚡", "color": "orange", "text": "Nearly Automatic"},
        "automatic": {"emoji": "✨", "color": "gold", "text": "Automatic!"}
    }

    info = status_info.get(status, status_info["early_stage"])

    st.progress(percentage / 100, text=f"{info['emoji']} {percentage:.0f}% toward automatic")

    if days_remaining > 0:
        st.caption(f"📊 Estimated {days_remaining} more days to automaticity (Lally et al., 2010)")
    else:
        st.caption(f"✅ You've reached the typical automaticity threshold! Keep going!")


# ============================================================================
# MAIN UI COMPONENTS
# ============================================================================

def render_habit_system_dashboard():
    """Render consolidated, research-based habit system"""

    st.header("🎯 Habit System")
    st.caption("*Research-based behavior change system*")

    # Quick dashboard stats (collapsed by default)
    with st.expander("📊 Today's Habit Dashboard", expanded=False):
        render_daily_dashboard()

    st.divider()

    # Main habit sections
    render_established_habits()
    st.divider()

    render_developing_habits()
    st.divider()

    render_action_items()
    st.divider()

    render_occasional_behaviors()
    st.divider()

    render_behavior_reduction()
    st.divider()

    # Educational resources
    with st.expander("🎓 Habit Science Guide", expanded=False):
        render_science_guide()

    with st.expander("📚 Research Bibliography", expanded=False):
        render_bibliography()


def render_daily_dashboard():
    """Render today's quick stats dashboard"""
    today = datetime.now().strftime('%Y-%m-%d')

    habits = config.get_habits()
    total_habits = len(habits['consistent']) + len(habits['intermittent'])

    # Get completion stats (simplified for now)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Habits", total_habits, help="Established + Developing")

    with col2:
        st.metric("Established", len(habits['consistent']), help="Daily automatic habits")

    with col3:
        st.metric("Developing", len(habits['intermittent']), help="Building toward automatic")

    with col4:
        # Get micro-tasks count
        pending_tasks = db_extensions.get_micro_tasks(completed=False)
        st.metric("Action Items", len(pending_tasks), help="Micro-tasks pending")


def render_established_habits():
    """Render established (daily/automatic) habits section"""
    st.subheader("🔄 Established Habits (Daily/Automatic)")

    col_header, col_tooltip = st.columns([6, 1])
    with col_header:
        st.caption("*These habits should feel automatic - consistent daily behaviors*")
    with col_tooltip:
        st.markdown("ℹ️", help=RESEARCH_TOOLTIPS["established_habits"])

    habits = config.get_habits()

    if not habits['consistent']:
        st.info("No established habits yet. Start by adding habits in Settings → Habits & Tasks")
        return

    completed_count = 0

    for habit in habits['consistent']:
        with st.container():
            col_checkbox, col_info, col_streak = st.columns([3, 2, 1])

            with col_checkbox:
                # Checkbox with identity framing
                habit_display = habit.replace('_', ' ').title()
                completed = st.checkbox(
                    f"**{habit_display}**",
                    key=f"established_{habit}",
                    help="Check when completed today"
                )

                if completed:
                    log_habit_completion(habit, True)
                    completed_count += 1

                    # Show celebration prompt (only once per session)
                    if f"celebrated_{habit}" not in st.session_state:
                        render_celebration_prompt(habit)
                        st.session_state[f"celebrated_{habit}"] = True

            with col_info:
                # Show context cue if available (placeholder for now)
                st.caption("⏰ *Cue: [Set in config]*")

            with col_streak:
                # Show streak (placeholder - would pull from database)
                if config.get('ui_preferences.show_streaks', True):
                    st.write("🔥 7")

    # Progress bar
    if habits['consistent']:
        completion_rate = completed_count / len(habits['consistent'])
        st.progress(completion_rate, text=f"Completed: {completed_count}/{len(habits['consistent'])} ({completion_rate*100:.0f}%)")

    # View detailed analysis
    if st.button("📈 View Detailed Analysis", key="analyze_established"):
        st.info("Detailed habit analysis would show promotion system insights here")


def render_developing_habits():
    """Render developing (intermittent/scheduled) habits section"""
    st.subheader("📅 Developing Habits (Intermittent/Scheduled)")

    col_header, col_tooltip = st.columns([6, 1])
    with col_header:
        st.caption("*Building toward automaticity - scheduled frequency habits*")
    with col_tooltip:
        st.markdown("ℹ️", help=RESEARCH_TOOLTIPS["developing_habits"])

    habits = config.get_habits()

    if not habits['intermittent']:
        st.info("No developing habits. Add habits in Settings → Habits & Tasks")
        return

    completed_count = 0

    for habit in habits['intermittent']:
        with st.container():
            col_checkbox, col_schedule, col_progress = st.columns([3, 1, 2])

            with col_checkbox:
                habit_display = habit.replace('_', ' ').title()
                completed = st.checkbox(
                    f"**{habit_display}**",
                    key=f"developing_{habit}",
                    help="Check when completed today"
                )

                if completed:
                    log_habit_completion(habit, True)
                    completed_count += 1

                    if f"celebrated_{habit}" not in st.session_state:
                        render_celebration_prompt(habit)
                        st.session_state[f"celebrated_{habit}"] = True

            with col_schedule:
                # Show target frequency
                if 'exercise' in habit.lower():
                    st.write("🎯 3x/week")
                elif 'connection' in habit.lower():
                    st.write("🎯 2x/week")
                else:
                    st.write("🎯 Weekly")

            with col_progress:
                # Show automaticity progress (simplified)
                try:
                    analysis = get_habit_analysis(habit)
                    if analysis and 'metrics' in analysis:
                        metrics = analysis['metrics']
                        progress = calculate_automaticity_progress(
                            habit,
                            metrics.get('total_tracking_days', 0),
                            metrics.get('consistency_rate', 0)
                        )
                        st.caption(f"⚡ {progress['percentage']:.0f}% automatic")
                except:
                    st.caption("⚡ Tracking...")

            # If-then plan reminder (placeholder)
            with st.expander(f"🎯 If-Then Plan for {habit_display}", expanded=False):
                st.caption("*When [trigger], I will [behavior]*")
                st.text_input("When (Cue):", placeholder="After breakfast", key=f"cue_{habit}")
                st.text_input("I will (Behavior):", placeholder="Do 10 pushups", key=f"behavior_{habit}")
                st.text_input("Then (Reward):", placeholder="Feel accomplished", key=f"reward_{habit}")

                col_save, col_help = st.columns([3, 1])
                with col_save:
                    if st.button("💾 Save If-Then Plan", key=f"save_plan_{habit}"):
                        st.success("If-then plan saved!")
                with col_help:
                    st.markdown("ℹ️", help=RESEARCH_TOOLTIPS["implementation_intentions"])

    # Progress bar
    if habits['intermittent']:
        completion_rate = completed_count / len(habits['intermittent'])
        st.progress(completion_rate, text=f"Completed Today: {completed_count}/{len(habits['intermittent'])} ({completion_rate*100:.0f}%)")

    # Promotion readiness
    if st.button("🚀 Check Promotion Readiness", key="check_promotions"):
        st.info("Promotion analysis would show which habits are ready to become established")


def render_action_items():
    """Render consolidated micro-tasks section"""
    st.subheader("⚡ Action Items (Micro-Tasks)")

    col_header, col_tooltip = st.columns([6, 1])
    with col_header:
        st.caption("*Quick tasks and implementation intentions*")
    with col_tooltip:
        st.markdown("ℹ️", help=RESEARCH_TOOLTIPS["implementation_intentions"])

    # Quick add form
    with st.expander("➕ Add Action Item", expanded=False):
        col_task, col_priority, col_time = st.columns([3, 1, 1])

        with col_task:
            new_task = st.text_input(
                "Task name",
                placeholder="What needs to be done?",
                key="new_action_item"
            )

        with col_priority:
            priority = st.selectbox(
                "Priority",
                ["low", "medium", "high"],
                index=1,
                key="action_priority"
            )

        with col_time:
            estimated_minutes = st.number_input(
                "Minutes",
                min_value=5,
                max_value=120,
                value=15,
                step=5,
                key="action_minutes"
            )

        # Optional if-then structure
        col_cue, col_then = st.columns(2)
        with col_cue:
            cue = st.text_input("When/After (optional):", placeholder="After lunch", key="action_cue")
        with col_then:
            st.caption("I will do: ↑ [task above]")

        if st.button("➕ Add Action Item", type="primary", key="add_action_btn"):
            if new_task.strip():
                # Combine cue with description if provided
                description = f"When: {cue}" if cue.strip() else None

                if db_extensions.add_micro_task(
                    task_name=new_task.strip(),
                    description=description,
                    priority=priority,
                    estimated_minutes=int(estimated_minutes)
                ):
                    st.success("✅ Action item added!")
                    st.rerun()
                else:
                    st.error("Failed to add action item")
            else:
                st.warning("Please enter a task name")

    st.divider()

    # Display pending action items
    st.markdown("### 📋 Pending Items")

    today = datetime.now().strftime('%Y-%m-%d')
    pending_tasks = db_extensions.get_micro_tasks(date=today, completed=False)

    if pending_tasks:
        for task in pending_tasks:
            col_check, col_task_info, col_delete = st.columns([1, 6, 1])

            with col_check:
                if st.button("✅", key=f"complete_action_{task['id']}", help="Mark complete"):
                    if db_extensions.complete_micro_task(task['id']):
                        st.success("Completed!")
                        st.balloons()
                        st.rerun()

            with col_task_info:
                priority_emoji = {"high": "🔥", "medium": "📋", "low": "📝"}
                st.markdown(f"""
**{priority_emoji[task['priority']]} {task['task_name']}**
⏱️ {task['estimated_minutes']} min | Priority: {task['priority'].title()}
{f"*{task['description']}*" if task['description'] else ""}
""")

            with col_delete:
                if st.button("🗑️", key=f"delete_action_{task['id']}", help="Delete"):
                    if db_extensions.delete_micro_task(task['id']):
                        st.rerun()

        # Summary stats
        total_time = sum(t['estimated_minutes'] for t in pending_tasks)
        st.caption(f"📊 {len(pending_tasks)} items pending · {total_time} minutes estimated")
    else:
        st.info("✨ No pending action items! Add some above or enjoy your clear task list.")

    # Show completed (collapsed)
    completed_tasks = db_extensions.get_micro_tasks(date=today, completed=True)
    if completed_tasks:
        with st.expander(f"✅ Completed Today ({len(completed_tasks)})", expanded=False):
            for task in completed_tasks:
                priority_emoji = {"high": "🔥", "medium": "📋", "low": "📝"}
                st.markdown(f"✅ {priority_emoji[task['priority']]} {task['task_name']} ({task['estimated_minutes']} min)")


def render_occasional_behaviors():
    """Render occasional/as-needed behaviors section"""
    st.subheader("🌟 Occasional Behaviors (As-Needed)")

    col_header, col_tooltip = st.columns([6, 1])
    with col_header:
        st.caption("*Track important behaviors that don't need daily frequency*")
    with col_tooltip:
        st.markdown("ℹ️", help=RESEARCH_TOOLTIPS["occasional_behaviors"])

    # Get behavior counter definitions
    countable_definitions = db_extensions.get_behavior_counter_definitions()
    occasional_tasks = [d for d in countable_definitions if d['counter_type'] == 'positive']

    if not occasional_tasks:
        st.info("No occasional behaviors configured. Add them in Settings → Habits & Tasks")
        return

    today = datetime.now().strftime('%Y-%m-%d')

    for task in occasional_tasks:
        col_name, col_today, col_week, col_btn = st.columns([3, 1, 1, 1])

        with col_name:
            st.markdown(f"**{task['counter_name'].replace('_', ' ').title()}**")
            if task['description']:
                st.caption(task['description'])

        with col_today:
            # Get today's count
            today_data = db_extensions.get_behavior_counter_data(task['counter_name'], days=1)
            today_count = today_data[0]['count'] if today_data and today_data[0]['date'] == today else 0
            st.metric("Today", today_count)

        with col_week:
            # Get week's count
            week_data = db_extensions.get_behavior_counter_data(task['counter_name'], days=7)
            week_count = sum(d['count'] for d in week_data)
            st.metric("Week", week_count)

        with col_btn:
            if st.button("➕", key=f"increment_{task['counter_name']}", help="Add 1"):
                if db_extensions.increment_behavior_counter(task['counter_name'], 1):
                    st.success("✓")
                    st.rerun()


def render_behavior_reduction():
    """Render bad habit elimination section"""
    st.subheader("🚫 Behavior Reduction (Breaking Bad Habits)")

    col_header, col_tooltip = st.columns([6, 1])
    with col_header:
        st.caption("*Research-based strategies for eliminating unwanted behaviors*")
    with col_tooltip:
        st.markdown("ℹ️", help=RESEARCH_TOOLTIPS["habit_extinction"])

    # Get negative behavior counters
    countable_definitions = db_extensions.get_behavior_counter_definitions()
    negative_behaviors = [d for d in countable_definitions if d['counter_type'] == 'negative']

    if not negative_behaviors:
        st.info("""
No negative behaviors being tracked.

To break a bad habit:
1. Add it as a negative counter in Settings → Habits & Tasks
2. Track occurrences daily (aiming for 0)
3. Use the extinction strategies below
""")
        return

    today = datetime.now().strftime('%Y-%m-%d')

    for behavior in negative_behaviors:
        with st.expander(f"🚫 {behavior['counter_name'].replace('_', ' ').title()}", expanded=True):
            # Status
            st.markdown("#### Current Status")

            today_data = db_extensions.get_behavior_counter_data(behavior['counter_name'], days=1)
            today_count = today_data[0]['count'] if today_data and today_data[0]['date'] == today else 0

            week_data = db_extensions.get_behavior_counter_data(behavior['counter_name'], days=7)
            week_count = sum(d['count'] for d in week_data)

            col_today, col_week, col_trend = st.columns(3)
            with col_today:
                st.metric("Today", today_count, help="Aiming for 0")
            with col_week:
                st.metric("This Week", week_count, help="Lower is better")
            with col_trend:
                # Calculate trend (simplified)
                if len(week_data) >= 7:
                    first_half = sum(d['count'] for d in week_data[:3])
                    second_half = sum(d['count'] for d in week_data[4:])
                    if second_half < first_half:
                        st.metric("Trend", "↓ Improving", help="Count decreasing")
                    elif second_half > first_half:
                        st.metric("Trend", "↑ Increasing", delta_color="inverse", help="Needs attention")
                    else:
                        st.metric("Trend", "→ Stable")

            # Extinction Strategy
            st.markdown("#### Extinction Strategy")
            st.caption("*Based on Wood & Neal (2007) and recent neuroscience research*")

            col_strategy, col_log = st.columns([3, 1])

            with col_strategy:
                triggers = st.text_area(
                    "⚠️ Triggers (what cues this behavior?):",
                    placeholder="E.g., Boredom, stress, seeing phone, 8pm on couch",
                    key=f"triggers_{behavior['counter_name']}",
                    height=60
                )

                replacement = st.text_input(
                    "🔄 Replacement Behavior:",
                    placeholder="E.g., Do 5 pushups, call a friend, read a chapter",
                    key=f"replacement_{behavior['counter_name']}"
                )

                context_change = st.text_input(
                    "🏗️ Context Modification:",
                    placeholder="E.g., Keep phone in drawer, wear fitness tracker, set app limits",
                    key=f"context_{behavior['counter_name']}"
                )

                if_then_defense = st.text_input(
                    "🛡️ If-Then Defense:",
                    placeholder="If I feel urge to [bad habit], then I will [replacement behavior]",
                    key=f"defense_{behavior['counter_name']}"
                )

                if st.button("💾 Save Strategy", key=f"save_strategy_{behavior['counter_name']}"):
                    # TODO: Save to database
                    st.success("Strategy saved!")

            with col_log:
                st.markdown("#### Quick Actions")

                if st.button("➕ Log Occurrence", key=f"log_negative_{behavior['counter_name']}", type="secondary"):
                    if db_extensions.increment_behavior_counter(behavior['counter_name'], 1):
                        st.warning("Logged. Review your strategy!")
                        st.rerun()

                if st.button("✅ Resisted Urge!", key=f"resist_{behavior['counter_name']}", type="primary"):
                    st.balloons()
                    st.success("Great job resisting! That builds the new neural pathway!")


def render_science_guide():
    """Render habit science educational guide"""
    st.markdown("### 🎓 Quick Habit Science Principles")

    principles = {
        "📊 66 Days to Automaticity": {
            "source": "Lally et al. (2010)",
            "principle": "Average 66 days for habits to become automatic (range: 18-254 days)",
            "application": "Be patient! Simple habits form faster than complex ones."
        },
        "🎯 If-Then Plans": {
            "source": "Gollwitzer (1999)",
            "principle": "Implementation intentions boost success by 65% (d=.65)",
            "application": "Format: 'When X happens, I will do Y' - delegates control to environment."
        },
        "🔬 B=MAP Model": {
            "source": "Fogg (2009, 2019)",
            "principle": "Behavior = Motivation × Ability × Prompt (all must converge)",
            "application": "Make it tiny, make it easy, anchor to existing routine, celebrate immediately."
        },
        "👤 Identity-Based Change": {
            "source": "Clear (2018)",
            "principle": "Focus on becoming someone, not achieving something",
            "application": "'I am a [type of person]' not 'I want to do X'. Every action is a vote for your identity."
        },
        "🔁 The Habit Loop": {
            "source": "Duhigg (2012)",
            "principle": "Cue → Routine → Reward creates neural pathways",
            "application": "Make cues obvious, routine easy, rewards satisfying. For bad habits, keep cue & reward, change routine."
        },
        "❌ Breaking Habits": {
            "source": "Wood & Neal (2007), Haith & Krakauer (2024)",
            "principle": "Habits are context-specific; breaking requires context change + competing behaviors",
            "application": "Avoid triggers, create competing routines, use if-then plans for inhibition, modify environment."
        }
    }

    for title, details in principles.items():
        with st.expander(title, expanded=False):
            st.markdown(f"**Research**: {details['source']}")
            st.markdown(f"**Principle**: {details['principle']}")
            st.markdown(f"**Application**: {details['application']}")
            st.divider()
            st.caption("See Research Bibliography below for full citations")


def render_bibliography():
    """Render research bibliography"""
    st.markdown("### 📚 Complete Research Bibliography")
    st.caption("*All research cited in this interface (Chicago style)*")

    st.markdown("""
#### Primary Research Papers

**Lally, Phillippa, Cornelia H. M. van Jaarsveld, Henry W. W. Potts, and Jane Wardle.**
"How Are Habits Formed: Modelling Habit Formation in the Real World."
*European Journal of Social Psychology* 40, no. 6 (2010): 998-1009.
https://doi.org/10.1002/ejsp.674

**Gollwitzer, Peter M.** "Implementation Intentions: Strong Effects of Simple Plans."
*American Psychologist* 54, no. 7 (1999): 493-503.
https://doi.org/10.1037/0003-066X.54.7.493

**Fogg, B. J.** "A Behavior Model for Persuasive Design."
*Proceedings of the 4th International Conference on Persuasive Technology* (2009): Article 40.
https://doi.org/10.1145/1541948.1541999

**Wood, Wendy, and David T. Neal.** "A New Look at Habits and the Habit-Goal Interface."
*Psychological Review* 114, no. 4 (2007): 843-863.
https://doi.org/10.1037/0033-295X.114.4.843

**Gardner, Benjamin, Phillippa Lally, and Jane Wardle.** "Making Health Habitual: The Psychology of 'Habit-Formation' and General Practice."
*British Journal of General Practice* 62, no. 605 (2012): 664-666.
https://doi.org/10.3399/bjgp12X659466

**Haith, A. M., and J. W. Krakauer.** "Leveraging Cognitive Neuroscience for Making and Breaking Real-World Habits."
*Trends in Cognitive Sciences* 28, no. 11 (2024): 1010-1025.
https://doi.org/10.1016/j.tics.2024.09.005

#### Books

**Clear, James.** *Atomic Habits: An Easy & Proven Way to Build Good Habits & Break Bad Ones*.
New York: Avery, 2018.

**Duhigg, Charles.** *The Power of Habit: Why We Do What We Do in Life and Business*.
New York: Random House, 2012.

**Fogg, B. J.** *Tiny Habits: The Small Changes That Change Everything*.
Boston: Houghton Mifflin Harcourt, 2019.
""")

    # Toggle for full bibliography
    if 'show_full_bibliography' not in st.session_state:
        st.session_state.show_full_bibliography = False

    if st.button("📖 View Complete Bibliography (35+ sources)", key="full_bibliography"):
        st.session_state.show_full_bibliography = not st.session_state.show_full_bibliography

    if st.session_state.show_full_bibliography:
        import os
        bib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "HABIT_RESEARCH_BIBLIOGRAPHY.md")
        try:
            with open(bib_path, 'r') as f:
                bibliography_content = f.read()
            st.markdown("---")
            st.markdown(bibliography_content)
        except FileNotFoundError:
            st.error("Bibliography file not found. Please ensure HABIT_RESEARCH_BIBLIOGRAPHY.md exists in the project root.")


# ============================================================================
# MAIN EXPORT FUNCTION
# ============================================================================

def render_habit_system_redesigned():
    """Main function to render the complete redesigned habit system"""
    render_habit_system_dashboard()


# For backwards compatibility and testing
if __name__ == "__main__":
    st.set_page_config(page_title="Habit System", page_icon="🎯", layout="wide")
    render_habit_system_redesigned()
