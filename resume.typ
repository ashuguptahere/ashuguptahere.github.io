// Renders the resume PDF from data.yaml.
//
//   typst compile resume.typ Resume_Aashish_Gupta_AI_Engineer_Data_Scientist.pdf
//
// data.yaml holds candidate data only: plain values, no markup. Nothing in it
// is evaluated, so characters like # (C#) and & are always literal.
//
// Section order and section headings both come from the keys in data.yaml, so
// adding a section there needs no edit here beyond a rendering rule.

#let data = yaml("data.yaml")
#let basics = data.basics

// ------------------------------------------------------------------ document

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
  // Name and page position on every page, so a page separated from the rest
  // is still identifiable.
  footer: context {
    set text(size: 8pt, style: "italic")
    let last = str(counter(page).final().first())
    basics.name
    h(1fr)
    "Page " + str(here().page()) + " of " + last
  },
)

#set text(font: "New Computer Modern", size: 10pt)
#set par(justify: true, leading: 0.5em, spacing: 0.6em, first-line-indent: 0pt)
#show link: set text(fill: blue)

// Never break a line inside a hyphenated token: a break inside "RF-DETR" makes
// PDF text extraction emit "RFDETR", so an ATS never matches the keyword.
#set text(hyphenate: false)

// ---------------------------------------------------------------- components

#let section(title, body) = {
  // sticky: true glues the heading to the body that follows, so a heading can
  // never sit alone at the foot of a page with its content overleaf.
  // breakable: false keeps the title and its rule together.
  // `above` is the gap from the previous section, which reads as crowded when
  // the sections nearly touch.
  block(breakable: false, sticky: true, above: 13pt, below: 4pt)[
    #text(weight: "bold", upper(title))
    #v(3pt, weak: true)
    #line(length: 100%, stroke: 0.4pt)
  ]
  body
}

#let bullet_list(items) = list(
  marker: [•],
  indent: 0.6em,
  body-indent: 0.4em,
  spacing: 0.45em,
  ..items,
)

// Only hyphenated terms need protecting. Multi-word terms may wrap freely -
// extraction normalises the newline back to a space - and leaving them
// breakable keeps justified lines from stretching.
#let nobreak(s) = if "-" in s { box(s) } else { s }

// Harvard entry: organisation bold with location right-aligned, then role
// italic with dates right-aligned, then the role's stack on one line.
#let dated_entry(job) = block(spacing: 0.4em)[
  #strong(job.company) #h(1fr) #job.location \
  #emph(if "role_url" in job { link(job.role_url)[#job.role] } else { job.role })
  #h(1fr) #job.dates
  #if "stack" in job [ \ #strong("Stack: ") #job.stack.map(nobreak).join(", ") ]
]

// data.yaml's shared shape: name / url? / detail? / links?.
#let entry_line(e) = {
  let head = if "url" in e { link(e.url)[#e.name] } else { strong(e.name) }
  let out = if "detail" in e [#head: #e.detail] else [#head]
  if "links" in e {
    let ls = e.links.map(l => link(l.url)[#l.name]).join(", ")
    out = [#out. #e.at("links_label", default: "Links"): #ls]
  }
  out
}

// One rendering rule per section key in data.yaml.
#let render(key, value) = {
  if key == "summary" {
    value
  } else if key == "experience" {
    for job in value {
      dated_entry(job)
      bullet_list(job.bullets)
      v(0.3em)
    }
  } else if key == "education" {
    for e in value {
      block(spacing: 0.4em)[#e.degree #emph(" from ") #e.institution #h(1fr) #e.dates]
    }
  } else if key == "skills" {
    // One bullet per category, as plain text rather than a table: PDF text
    // extraction splits table cells from their row labels.
    bullet_list(value.map(s => [
      #strong(s.category + ":") #s.items.map(nobreak).join(", ")
    ]))
  } else if key in ("patents", "projects", "achievements", "certifications") {
    // Single column throughout: multi-column reading order is fragile under
    // PDF text extraction.
    bullet_list(value.map(entry_line))
  } else {
    // leadership, activities, and any future list of plain statements.
    bullet_list(value)
  }
}

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
  // Boxed so a URL is never split across lines mid-path.
  #{
    let parts = ()
    // Phone is optional: rendered only when data.yaml carries one, so an empty
    // field leaves no stray separator behind.
    let phone = basics.at("phone", default: "")
    if phone != "" { parts.push(box(phone)) }
    parts.push(box(link("mailto:" + basics.email)[#basics.email]))
    for l in basics.links {
      parts.push(box(link(l.url)[#l.at("display", default: l.label)]))
    }
    parts.join([ #sym.dot.c ])
  }
]

#v(0.2em)

// ------------------------------------------------------------------ sections

#for (key, value) in data.pairs().filter(p => p.first() != "basics") {
  section(key, render(key, value))
}
