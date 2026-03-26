# Arsh Wafiq Khan Chowdhury

**Technology Consultant — Sydney, NSW**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-arsh--wafiq--khan--chowdhury-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/arsh-wafiq-khan-chowdhury)
[![Email](https://img.shields.io/badge/Email-arshwafiq%40gmail.com-D14836?style=flat&logo=gmail&logoColor=white)](mailto:arshwafiq@gmail.com)
[![Location](https://img.shields.io/badge/Location-Sydney%2C%20NSW-lightgrey?style=flat)](#)

---

I started in UX. Spent years thinking about how people interact with systems, what makes something intuitive, and what makes someone abandon a tool halfway through a task. At some point I realised the more interesting version of that question was upstream: why does the system exist at all, and is it solving the right problem?

That pulled me toward consulting. I now work across solution design, business analysis, and implementation with a growing focus on AI-assisted automation and agent architecture. The UX background didn't go away; it just moved into how I run discovery workshops and how I think about adoption before anything gets built.

---

## What I work with

**Power Platform:** Power Apps (canvas and model-driven), Power Automate, Power BI, Copilot Studio, Dataverse, Dynamics 365

**Azure:** Azure OpenAI (GPT-4o), Azure AI Search, Azure App Service, Azure SQL, Microsoft Entra ID, Application Insights, Bicep IaC, Key Vault, Blob Storage

**Business Analysis:** Requirements workshops, BPMN 2.0, SIPOC, Value Stream Mapping, gap analysis, solution documentation, stakeholder management

**Development:** React, HTML/CSS/JavaScript, Python (pandas, scikit-learn, RAG pipelines), SQL

**Design:** Figma, wireframing, UX research, usability testing

---

## Live Projects

**[Microsoft AI Agent Readiness Assessment](https://microsoft-readiness-tool.vercel.app/)**: Pre-engagement discovery tool that evaluates whether an organisation is positioned to deploy Microsoft Copilot Studio or Azure AI agents. Evaluates five weighted dimensions (Process Foundation 25%, Data and Knowledge 25%, Microsoft Platform 20%, AI Governance 15%, Change Readiness 15%) and maps results to one of seven deployment archetypes, each identifying specifically where the constraint sits, not just how mature the organisation is. Each archetype includes a dynamically generated binding constraint analysis and a three-phase engagement pathway. Includes two practitioner-specific questions targeting failure modes common in Microsoft AI deployments: Power Platform environment strategy and DLP policy compatibility with Copilot Studio. Produces a capability radar chart, benchmark indicator, and printable consulting brief formatted as a first-meeting deliverable. Results are shareable via URL. Built in React 19 + Vite, deployed on Vercel.

**[Portfolio Site](https://arshchowdhury.vercel.app/)** — Personal site with case studies, skills, and contact. Built in React, deployed on Vercel.

**[Australian ICT & Digital Workforce Dashboard](https://arsh-ict-dashboard.vercel.app/)** — Market intelligence dashboard visualising ICT job demand, salaries, skills, and emerging roles using public Australian data. React + Recharts.

**[BA Process Documentation Generator](https://arsh-ba-automation-tool.vercel.app/)** — AI-powered tool that generates SIPOC tables, discovery questions, pain points, and framework recommendations from a process description. Uses Groq API (free tier).

---

## Case Studies

### [Room Booking — Platform Evaluation and Migration](./consulting-case-studies/01-room-booking-platform-migration/)
*Live engagement · Facilities Management / Co-working · Sydney*

The company proposed rebuilding a dated room booking system on Microsoft Power Apps. I evaluated the proposal against the client's actual constraints — front-desk hardware performance, licensing cost for casual users, UX flexibility requirements — and recommended against it. Built a custom React web application on a local Apache server instead, with a self-service Admin Panel to address the low-code maintainability argument. Scoped and documented the Azure migration architecture (App Service, Azure SQL, Entra ID) for the client's next growth phase.

`React` `HTML/CSS/JS` `Apache` `Power Apps evaluation` `Azure migration roadmap`

---

### [Sales Pipeline Dashboard — Summit Advisory](./consulting-case-studies/02-sales-pipeline-power-bi/)
*Designed case study · Professional Services*

A consulting firm running their pipeline out of manually exported Excel files. Replaced with a live Power BI dashboard connected directly to Dynamics 365. Gap analysis surfaced that the root problem was the data source, not the report format. Includes DAX for weighted pipeline, rolling win rate, stage conversion, and deal cycle time. RLS for BD staff self-service.

`Power BI` `Dynamics 365` `DAX` `RLS`

---

### [Digital Intake Automation — Clearpath Health](./consulting-case-studies/03-clearpath-health-intake/)
*Designed case study · Healthcare / Community Services*

A community health provider processing new patient intake on paper, with staff manually re-entering data. Digitised the form, automated data flows to the PMS via API, and added an AI-assisted accessibility agent (Copilot Studio) for patients with low English literacy — a scope gap that surfaced in the discovery workshop, not the original brief.

`Power Apps` `Power Automate` `Azure OpenAI` `Copilot Studio`

---

## AI Agent Designs

Three industry-specific agents built on Azure OpenAI, Copilot Studio, and Power Automate. Infrastructure via Bicep templates. Design philosophy: business problem first, governance as a first-class concern, mandatory human escalation paths.

### [Query AI Assistant](./Ai-Agent-Design/Query-AI-Assistant/) — Financial Services
Policy query resolution. Python RAG pipeline, Azure AI Search grounding, token-aware chunking, confidence-based routing. Built for environments where an incorrect answer carries regulatory consequence.

### [CareAssist Incident Agent](./Ai-Agent-Design/CareAssist-AI-Agent/) — Aged Care
Clinical incident triage via Teams. GPT-4o classifies by severity, category, and regulatory flag in real time. Three-tier Power Automate escalation. Immutable SharePoint audit trail for Aged Care Act compliance. Australia East datacentres.

### [RetailIQ Sales Agent](./Ai-Agent-Design/RetailIQ-AI-Agent/) — Retail / eCommerce
Multi-channel sales agent across Teams and web. Handles product queries, stock availability, order status. Power Automate follow-up integration. Confidence threshold routing escalates ambiguous queries to human staff.

---

## Workflow Automation

### [Automated Document Processing](./Workflow-Automation-Case-Studies/Automated-Document-Processing/)
Confidence-based routing for AI-augmented document handling. High-confidence items processed automatically; low-confidence escalated for human review. Built on the principle that automation should shrink the queue, not replace the judgment call.

---

## Solution Design and Process Work

**[Truefield Aged Care — M365 Transformation](./solution-design-work/Truefield%20Aged%20Care/)**
End-to-end solution design for a Microsoft 365 transformation: governance, information architecture, Teams deployment, change management.

**[Retail Catalogue Management — Process Mapping](./Process%20Mapping/retail-catalogue-management/)**
BPMN 2.0 swim lane diagrams and SIPOC for a retail catalogue workflow. Current state mapping, pain point analysis, future state design.

---

## Certifications

- SAP Certified — Professionals Fundamentals
- Google Project Management Certificate, Intro to Generative AI 
- AWS Cloud Certificate 
- IBM - Exploratory Data Analysis for Machine Learning, Python for Data Science, AI and Development, Data Science Methodology, Tools for Data Science V2, Data Science Orientation,
- Hubspot - Digital Advertising, Inbound Marketing, Content Marketing, Social Media Marketing, SEO, Digital Marketing.

**Currently working toward:**
- AI-102: Azure AI Engineer Associate — exam booked April 2026
- PL-200: Microsoft Power Platform Functional Consultant
- PL-900: Microsoft Power Platform Fundamentals

---

## Education

**Master of Commerce (Extension)** — UNSW Sydney
Business Analytics and Digital Transformation · WAM 79, Distinction

**Bachelor of Business and Commerce** — Monash University
First Class Honours

---

Open to technology consultant, implementation consultant, and BA roles in Australia.
**arshwafiq@gmail.com** · [linkedin.com/in/arsh-wafiq-khan-chowdhury](https://linkedin.com/in/arsh-wafiq-khan-chowdhury)




