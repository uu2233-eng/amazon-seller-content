"""
Prompt 模板库

为不同内容格式（图文、短视频、长视频、社交帖子、图片）定义 LLM prompt 模板。
"""


class PromptTemplates:

    TOPIC_LABEL = """You are a content strategist specializing in Amazon seller education.

Given the following cluster of related content items, generate a concise topic label (5-10 words) that captures the core theme.

Content titles in this cluster:
{titles}

Representative content body:
{body}

Respond with ONLY the topic label, nothing else."""

    ARTICLE = """You are an expert content creator for Amazon sellers. Based on the trending topic below, create a compelling article outline and draft.

## Trending Topic
{topic_summary}

## Target Audience
{audience_description}

## Requirements
Create a complete article with:

1. **Title**: A compelling, SEO-friendly headline (include power words, numbers if appropriate)
2. **Subtitle**: A supporting subheadline
3. **Hook**: Opening paragraph that grabs attention (2-3 sentences)
4. **Outline**: 5-7 main sections with key points for each
5. **Key Takeaways**: 3-5 bullet points summarizing the article
6. **CTA**: Call to action for the reader
7. **SEO Keywords**: 5-8 target keywords

Write in a professional yet conversational tone. Include actionable advice and real examples where possible.
Format the output in Markdown."""

    SHORT_VIDEO = """You are a viral short-form video scriptwriter specializing in Amazon seller content.

## Trending Topic
{topic_summary}

## Target Audience
{audience_description}

## Requirements
Create a 60-second short video script (for YouTube Shorts / TikTok / Instagram Reels):

1. **Title**: Catchy title with emoji hooks
2. **Hook** (0-3 seconds): Opening line that stops the scroll. Must create curiosity or urgency.
3. **Problem** (3-10 seconds): State the pain point clearly
4. **Solution/Content** (10-45 seconds): Deliver the main value in 3-5 punchy points
5. **CTA** (45-60 seconds): Strong call to action
6. **On-screen text suggestions**: Key text overlays for each section
7. **B-roll / Visual suggestions**: What to show on screen for each section
8. **Hashtags**: 10-15 relevant hashtags
9. **Thumbnail concept**: Describe the ideal thumbnail

Write in a high-energy, direct tone. Every sentence should be short and impactful.
Format the output in Markdown."""

    LONG_VIDEO = """You are an expert YouTube content strategist for the Amazon seller niche.

## Trending Topic
{topic_summary}

## Target Audience
{audience_description}

## Requirements
Create a detailed 8-12 minute YouTube video script:

1. **Title**: SEO-optimized title (include year, power words)
2. **Description**: YouTube description with timestamps, links, and keywords
3. **Tags**: 15-20 YouTube tags

4. **SCRIPT**:
   - **Cold Open / Hook** (0:00 - 0:30): Dramatic opening that previews the value
   - **Intro / Branding** (0:30 - 1:00): Channel intro, establish credibility
   - **Context / Why This Matters** (1:00 - 2:00): Why this topic is relevant NOW
   - **Main Content** (2:00 - 8:00): 3-5 main sections, each with:
     - Section title
     - Key talking points
     - Screen recording / visual suggestions
     - Example or case study
   - **Common Mistakes** (8:00 - 9:30): 2-3 mistakes to avoid
   - **Action Steps** (9:30 - 10:30): Step-by-step what to do next
   - **CTA / Outro** (10:30 - 11:00): Subscribe, comment prompt, teaser for next video

5. **Thumbnail Concepts**: 2-3 thumbnail ideas with text overlay suggestions
6. **End Screen Strategy**: What to link to

Write in an engaging, educational tone. Include specific examples and data points.
Format the output in Markdown."""

    IMAGE_PROMPT = """You are a visual content director specializing in Amazon seller educational content.

## Trending Topic
{topic_summary}

## Target Audience
{audience_description}

## Requirements
Generate 5 AI image prompts for different use cases. Each prompt should be detailed and ready to paste into Midjourney, DALL-E, or Stable Diffusion.

For each image, provide:
1. **Use Case**: (thumbnail / blog header / social media post / infographic / carousel slide)
2. **Prompt**: Detailed image generation prompt (include style, lighting, composition, colors, mood)
3. **Negative Prompt**: What to avoid
4. **Aspect Ratio**: Recommended ratio (16:9, 1:1, 9:16, 4:5)
5. **Text Overlay Suggestion**: What text to add on top of the image afterwards

Style guidelines:
- Professional yet approachable
- Clean, modern aesthetic
- Brand colors: deep blue, orange accents, white backgrounds
- Avoid stock photo clichés

Format the output in Markdown."""

    SOCIAL_POST = """You are a social media strategist for Amazon seller communities.

## Trending Topic
{topic_summary}

## Target Audience
{audience_description}

## Requirements
Create social media posts for 4 platforms:

### 1. Twitter/X Thread (5-7 tweets)
- Tweet 1: Hook with a bold statement or surprising stat
- Tweets 2-6: Value-packed tips, each can stand alone
- Final tweet: CTA + link placeholder
- Include relevant emojis sparingly

### 2. LinkedIn Post
- Professional tone
- Personal story or insight angle
- Include 3-5 relevant hashtags
- End with engagement question

### 3. Facebook Group Post
- Conversational, community-oriented tone
- Ask for opinions/experiences
- Include value upfront

### 4. Instagram Carousel (8-10 slides)
- Slide 1: Bold title slide
- Slides 2-9: One key point per slide with brief explanation
- Slide 10: CTA slide
- Caption with hashtags

Format the output in Markdown."""

    @classmethod
    def get_template(cls, format_type: str) -> str:
        templates = {
            "article": cls.ARTICLE,
            "short_video": cls.SHORT_VIDEO,
            "long_video": cls.LONG_VIDEO,
            "image_prompt": cls.IMAGE_PROMPT,
            "social_post": cls.SOCIAL_POST,
        }
        return templates.get(format_type, cls.ARTICLE)

    @classmethod
    def available_formats(cls) -> list[str]:
        return ["article", "short_video", "long_video", "image_prompt", "social_post"]
