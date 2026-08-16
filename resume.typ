// Resume template — renders data.yaml to PDF.
//
//   typst compile resume.typ Resume_Aashish_Gupta_AI_Engineer_Data_Scientist.pdf
//
// Replaces the former LaTeX pair (resume.cls + a .tex driving an embedded
// 166-line Lua YAML parser); Typst reads YAML natively.

#let data = yaml("data.yaml")

// data.yaml holds pure data: no markup, nothing evaluated. Every string is
// inserted verbatim, so characters like # (C#) and & are always literal.
//
// Emphasis is applied here instead: any phrase listed under `emphasize` in
// data.yaml is shown in bold wherever it appears in a bullet.
#let stress(s) = {
  let parts = (s,)
  for phrase in data.at("emphasize", default: ()) {
    parts = parts.map(p => if type(p) == str and phrase in p {
      p.split(phrase).intersperse(strong(phrase))
    } else { (p,) }).flatten()
  }
  parts.join()
}

#let basics = data.basics

// Keywords mirror the visible skills; some ATS read PDF metadata as well as
// page text.
#set document(
  title: basics.name + " - " + basics.headline,
  author: basics.name,
  // Maps to the PDF Subject field.
  description: basics.headline + " - " + basics.titles,
  keywords: data.skills.map(s => s.items).flatten(),
  // Omit the build timestamp so the PDF is byte-reproducible and a rebuild
  // with no content change leaves the working tree clean.
  date: none,
)

#set page(
  paper: "a4",
  margin: (x: 0.3in, top: 0.3in, bottom: 0.42in),
  // Name and "Page N of M" on every page: a page separated from the rest is
  // still identifiable.
  footer: context {
    set text(size: 8pt, style: "italic")
    basics.name
    h(1fr)
    "Page " + str(here().page()) + " of " + str(counter(page).final().first())
  },
)

#set text(font: "New Computer Modern", size: 10pt)
#set par(justify: true, leading: 0.5em, spacing: 0.6em, first-line-indent: 0pt)
#show link: set text(fill: blue)

// Never break a line inside a hyphenated token: a break inside "RF-DETR" or
// "edge-AI" makes PDF text extraction emit "RFDETR"/"edgeAI", so an ATS never
// matches the keyword.
#set text(hyphenate: false)

// ---------------------------------------------------------------- components

#let section(title, body) = {
  // Keep a heading with the start of its body so it never strands at a page
  // foot. `above` is the gap from the previous section's last line.
  block(breakable: false, above: 13pt, below: 4pt)[
    #text(weight: "bold", upper(title))
    #v(3pt, weak: true)
    #line(length: 100%, stroke: 0.4pt)
  ]
  body
}

// Takes already-built content.
#let bullet_list(items) = list(
  marker: [•],
  indent: 0.6em,
  body-indent: 0.4em,
  spacing: 0.45em,
  ..items,
)

// Plain sentences from data.yaml, with `emphasize` phrases bolded.
#let bullets(items) = bullet_list(items.map(stress))

// Only hyphenated terms need protecting: a break inside "RF-DETR" extracts as
// "RFDETR" and the ATS never matches it. Multi-word terms may wrap freely —
// extraction normalises the newline back to a space — and leaving them
// breakable keeps justified lines from stretching.
#let nobreak(s) = if "-" in s { box(s) } else { s }

// Harvard entry: organisation bold with location right-aligned, then title
// italic with dates right-aligned, then the role's stack on one line.
#let entry(org, location, title, dates, stack) = block(spacing: 0.4em)[
  #strong(org) #h(1fr) #location \
  #emph(title) #h(1fr) #dates
  // box() keeps a term unbreakable. Without it a line break inside "RF-DETR"
  // makes text extraction emit "RFDETR" and the ATS never matches it.
  #if stack != none [ \ #strong("Stack: ") #stack.map(nobreak).join(", ") ]
]

// -------------------------------------------------------------------- header

#align(center)[
  // Unjustified: the contact line is a row of unbreakable boxes, and
  // justifying it stretches the separators into ragged gaps.
  #set par(justify: false)
  #text(size: 17pt, weight: "bold", basics.name)

  #v(0.3em)

  #strong(basics.titles)

  #basics.location #sym.dot.c #basics.work_authorization

  // The URL itself is the link text: ATS read the text layer and almost never
  // follow link annotations, so "LinkedIn" would leave them with no URL.
  #{
    // Boxed so a URL is never split across lines mid-path.
    let parts = (box(link("mailto:" + basics.email)[#basics.email]),)
    for l in basics.links {
      parts.push(box(link(l.url)[#l.at("display", default: l.label)]))
    }
    parts.join([ #sym.dot.c ])
  }
]

#v(0.2em)

// ------------------------------------------------------------------ sections

#section("Summary")[#data.summary]

#section("Experience")[
  #for job in data.experience {
    let title = if "role_url" in job { link(job.role_url)[#job.role] } else { job.role }
    entry(job.company, job.location, title, job.dates, job.at("stack", default: none))
    bullets(job.bullets)
    v(0.3em)
  }
]

#section("Education")[
  #for e in data.education {
    block(spacing: 0.4em)[#e.degree #emph(" from ") #e.institution #h(1fr) #e.dates]
  }
]

#section("Skills & Interests")[
  // One bullet per category; plain text, not a table. Table cells get split
  // from their row labels by PDF text extraction. Built as content rather
  // than eval'd so "C#" stays literal.
  #bullet_list(data.skills.map(s => [#strong(s.category + ":") #s.items.map(nobreak).join(", ")]))
]

// Shared shape: name / url (optional) / detail (optional), plus an optional
// list of further links. Used by projects, achievements and certifications.
#let entry_line(e) = {
  let head = if "url" in e { link(e.url)[#e.name] } else { strong(e.name) }
  let out = if "detail" in e [#head: #e.detail] else [#head]
  if "links" in e {
    let ls = e.links.map(l => link(l.url)[#l.name]).join(", ")
    out = [#out. #e.at("links_label", default: "Links"): #ls]
  }
  out
}

#section("Projects")[#bullet_list(data.projects.map(entry_line))]

#section("Achievements")[#bullet_list(data.achievements.map(entry_line))]

#section("Leadership")[#bullets(data.leadership)]

#section("Activities")[#bullets(data.activities)]

// Single column: multi-column reading order is fragile under text extraction.
#section("Certifications")[
  #bullet_list(data.certifications.map(entry_line))
]
