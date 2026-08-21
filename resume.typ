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

// One margin for the whole page perimeter. The bottom is larger only because
// the footer band lives inside it: MARGIN + FOOTER_GAP + the footer's own line
// height, so the white paper *below the footer* still equals MARGIN and the
// border looks even on all four sides.
#let MARGIN = 0.3in
#let FOOTER_GAP = 10pt

#set page(
  paper: "a4",
  margin: (x: MARGIN, top: MARGIN, bottom: MARGIN + FOOTER_GAP + 6pt),
  // Distance from the body down to the footer.
  footer-descent: FOOTER_GAP,
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

// Every gap in the document is this, so headings, header lines and sections
// are all spaced identically. Tuned so the measured gap between the previous
// text line and the next one is ~9pt; block spacing is larger than the visible
// gap because line bounding boxes include ascender and descender room.
#let GAP = 12.1pt

// The header is five short centred lines, so the full section gap between
// them reads as too airy. It uses its own tighter value, applied to spacing
// AND leading so a wrapped contact line matches a separate one.
#let HEADER_GAP = 7.1pt

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
  block(breakable: false, sticky: true, above: GAP, below: 4pt)[
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
    // Spacer between jobs only: firing it after the last one added 3pt to
    // the gap before the next section heading.
    for (i, job) in value.enumerate() {
      dated_entry(job)
      bullet_list(job.bullets)
      if i + 1 < value.len() { v(0.3em) }
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
  // spacing AND leading are both GAP. The contact links wrap onto three
  // lines, and with the document's tighter leading those wrapped lines
  // clumped together while the lines above them sat GAP apart, which read as
  // uneven. Matching the two puts every header line on one rhythm.
  #set par(justify: false, spacing: HEADER_GAP, leading: HEADER_GAP)
  #text(size: 17pt, weight: "bold", basics.name)

  // The one deliberate exception: extra room under the name so it stands out.
  #v(3pt)

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

// ------------------------------------------------------------------ sections

#for (key, value) in data.pairs().filter(p => p.first() != "basics") {
  section(key, render(key, value))
}
