"""Multi-platform content synthesis engine with AI and deterministic template fallbacks."""

import logging
from typing import Any, Optional

from ai.analysis import ContentDraftSchema
from ai.provider import get_ai_provider

logger = logging.getLogger("opensource_radar.content")


class ContentGenerator:
    """Orchestrates educational content generation across platforms, languages, and formats."""

    @staticmethod
    def generate_deterministic_draft(
        repo_data: dict[str, Any],
        dossier: dict[str, Any],
        platform: str,
        content_type: str,
        language: str,
        tone: str,
        audience_level: str,
    ) -> ContentDraftSchema:
        """
        Generate high quality, evidence-based content draft deterministically
        without requiring external AI API calls.
        """
        name = repo_data.get("full_name", "OpenSource Project")
        desc = repo_data.get("description") or "high-impact open-source tool"
        stars = repo_data.get("stars", 0)
        url = repo_data.get("html_url", "https://github.com")
        
        claims = dossier.get("readme_claims", {})
        facts = dossier.get("verified_facts", {})
        obs = dossier.get("source_code_observations", {})
        tech = obs.get("detected_technologies", {})
        
        lang = facts.get("primary_language", "Python")
        problem = claims.get("problem_solved") or desc
        install_cmd = claims.get("installation_process") or f"git clone {url}"
        features = claims.get("features_claimed") or "Modular design, clean API, and open-source license."

        # Template adaptations for Language & Platform
        if language == "bn":
            title = f"{name}: ওপেন সোর্স প্রযুক্তির নতুন সম্ভাবনা"
            hook = f"আপনি কি জানেন {name} দিয়ে কীভাবে {problem[:80]} সমাধান করা যায়? বিস্তারিত জানুন এই বিশ্লেষণে!"
            body = (
                f"আজকে আমরা পর্যালোচনা করছি **{name}**—একটি শক্তিশালী ওপেন-সোর্স প্রকল্প "
                f"যা ইতিমধ্যে গিটহাবে {stars:,} স্টার অর্জন করেছে।\n\n"
                f"### এটি যে সমস্যার সমাধান করে:\n{problem}\n\n"
                f"### মূল বৈশিষ্ট্যসমূহ:\n{features}\n\n"
                f"### কীভাবে সেটআপ করবেন:\n```bash\n{install_cmd}\n```\n\n"
                f"প্রকল্পটি {lang} এ তৈরি এবং ডেভেলপারদের জন্য দারুণ একটি রিসোর্স।"
            )
            practical = f"এই প্রজেক্টটি ব্যবহার করে আপনি খুব সহজেই প্রোডাকশন গ্রেড সমাধান তৈরি করতে পারেন।"
            cta = f"সম্পূর্ণ কোড দেখতে এবং প্রজেক্টে স্টার দিতে ভিজিট করুন: {url}"
            hashtags = ["#ওপেনসোর্স", "#প্রোগ্রামিং", "#বাংলাটেক", f"#{lang}"]

        elif language == "banglish":
            title = f"{name} Review: Ei Open Source Tool Ki Apnar Kaaje Lagbe?"
            hook = f"GitHub e ekta darun open-source project pelam—{name}! {stars:,} stars already peye geche."
            body = (
                f"Ajke amra {name} niye kotha bolbo. Project ti main language hocche {lang}.\n\n"
                f"**Problem Solved:**\n{problem}\n\n"
                f"**Key Features:**\n{features}\n\n"
                f"**Setup Instruction:**\n```bash\n{install_cmd}\n```\n\n"
                f"Apnar development workflow e eta easily integrate korte parben."
            )
            practical = f"Directly install kore apnar codebase e import korun."
            cta = f"GitHub link theke code dekhe asun: {url}"
            hashtags = ["#BanglaTech", "#OpenSource", "#DevCommunity", f"#{lang}"]

        else:  # English default
            if "short" in platform.lower():
                title = f"Why Everyone Is Staring {name} on GitHub ({stars:,}⭐)"
                hook = f"Stop building this from scratch! Meet {name}—an open-source {lang} project taking over GitHub."
                body = (
                    f"Here is why {name} is worth your attention:\n"
                    f"1. Problem Solved: {problem[:140]}\n"
                    f"2. Built with {lang} and already trusted with {stars:,} stars.\n"
                    f"3. Quick setup:\n```bash\n{install_cmd[:120]}\n```"
                )
            elif "youtube" in platform.lower():
                title = f"{name} Deep Dive: Open-Source Architecture & Hands-on Walkthrough"
                hook = f"In today's video, we are breaking down {name}—an open-source project with {stars:,} stars that solves {problem[:80]}."
                body = (
                    f"## Video Script & Breakdown\n\n"
                    f"### [00:00 - 01:30] Introduction & The Problem\n"
                    f"Welcome back! Today we are examining {name}.\n{problem}\n\n"
                    f"### [01:30 - 05:00] Architecture & Under The Hood\n"
                    f"Built in {lang}, this repository showcases:\n{features}\n\n"
                    f"### [05:00 - 08:30] Installation & Hands-on Demo\n"
                    f"Let's jump into the terminal:\n```bash\n{install_cmd}\n```\n\n"
                    f"### [08:30 - 10:00] Verdict & Conclusion\n"
                    f"Overall, {name} provides an exceptional reference architecture."
                )
            elif "telegram" in platform.lower():
                title = f"Radar Alert: {name} ({stars:,}⭐)"
                hook = f"📡 **New Technology Radar Discovery**"
                body = (
                    f"**Repository**: [{name}]({url})\n"
                    f"**Stars**: ⭐ {stars:,} | **Language**: {lang}\n\n"
                    f"**Overview**:\n{desc}\n\n"
                    f"**Key Capability**:\n{problem[:200]}\n\n"
                    f"**Quick Run**:\n`{install_cmd[:100]}`"
                )
            else:  # Blog / Facebook / General
                title = f"Exploring {name}: An Open-Source {lang} Solution for Modern Engineers"
                hook = f"Discover how {name} brings clarity to {problem[:100]}."
                body = (
                    f"### Introduction\n"
                    f"OpenSource Radar is spotlighting **{name}**, a project with {stars:,} stars.\n\n"
                    f"### The Challenge\n{problem}\n\n"
                    f"### Architecture & Capabilities\n{features}\n\n"
                    f"### Getting Started\n```bash\n{install_cmd}\n```\n\n"
                    f"### Conclusion\n"
                    f"For engineers building with {lang}, this project demonstrates clean design and pragmatic utility."
                )

            practical = f"Inspect the source code at {url} and run the setup commands."
            cta = f"Check out the project on GitHub and drop a star if you find it helpful: {url}"
            hashtags = ["#OpenSource", "#SoftwareEngineering", f"#{lang}", "#TechRadar"]

        visuals = [
            f"Screen recording of terminal running: {install_cmd[:50]}",
            f"High-contrast thumbnail displaying: '{name}' logo and '{stars:,} Stars'",
            f"Architecture diagram animation demonstrating data flow",
        ]

        return ContentDraftSchema(
            platform=platform,
            content_type=content_type,
            language=language,
            tone=tone,
            audience_level=audience_level,
            title=title,
            hook=hook,
            body=body,
            practical_explanation=practical,
            visual_demo_suggestions=visuals,
            cta=cta,
            hashtags=hashtags,
            source_url=url,
        )

    def generate(
        self,
        repo_data: dict[str, Any],
        dossier: dict[str, Any],
        platform: str,
        content_type: str,
        language: str,
        tone: str,
        audience_level: str,
        additional_instructions: Optional[str] = None,
    ) -> tuple[ContentDraftSchema, str]:
        """
        Generate content draft using AI provider if available, otherwise deterministic templates.
        Returns: (draft_schema, generation_mode: 'ai_openai' | 'ai_gemini' | 'deterministic')
        """
        ai_provider = get_ai_provider()
        if ai_provider is not None:
            try:
                draft = ai_provider.generate_content(
                    repo_data=repo_data,
                    dossier=dossier,
                    platform=platform,
                    content_type=content_type,
                    language=language,
                    tone=tone,
                    audience_level=audience_level,
                    additional_instructions=additional_instructions,
                )
                from config import get_settings
                return draft, f"ai_{get_settings().AI_PROVIDER}"
            except Exception as exc:
                logger.warning(f"AI content generation failed ({exc}). Falling back to deterministic templates.")

        # Fallback to deterministic generation
        draft = self.generate_deterministic_draft(
            repo_data=repo_data,
            dossier=dossier,
            platform=platform,
            content_type=content_type,
            language=language,
            tone=tone,
            audience_level=audience_level,
        )
        return draft, "deterministic"


content_generator = ContentGenerator()
