"use client"

import type React from "react"
import { Document, Page, Text, View, StyleSheet, Font } from "@react-pdf/renderer"

// Register fonts
Font.register({
  family: "Times",
  src: "https://fonts.gstatic.com/s/timesnewroman/v18/4iCp6KVjbNBYlgoKejZftWyI.ttf",
})

// Create styles
const styles = StyleSheet.create({
  page: {
    padding: 50,
    fontFamily: "Times",
  },
  title: {
    fontSize: 16,
    fontWeight: "bold",
    textAlign: "center",
    marginBottom: 10,
  },
  authors: {
    fontSize: 12,
    textAlign: "center",
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "bold",
    marginTop: 15,
    marginBottom: 5,
  },
  paragraph: {
    fontSize: 12,
    lineHeight: 1.5,
    textAlign: "justify",
    marginBottom: 10,
  },
  abstract: {
    fontSize: 12,
    lineHeight: 1.5,
    textAlign: "justify",
    marginBottom: 20,
    marginTop: 10,
  },
  abstractTitle: {
    fontSize: 14,
    fontWeight: "bold",
    marginBottom: 5,
  },
  references: {
    fontSize: 12,
    lineHeight: 1.5,
    marginTop: 20,
  },
  referencesTitle: {
    fontSize: 14,
    fontWeight: "bold",
    marginBottom: 5,
    marginTop: 20,
  },
  referenceItem: {
    fontSize: 10,
    marginBottom: 5,
  },
  footer: {
    position: "absolute",
    bottom: 30,
    left: 0,
    right: 0,
    textAlign: "center",
    fontSize: 10,
    color: "grey",
  },
  pageNumber: {
    position: "absolute",
    bottom: 30,
    right: 50,
    fontSize: 10,
  },
})

interface PDFDocumentProps {
  title: string
  authors: string
  abstract?: string
  sections: Array<{
    title?: string
    paragraphs: string[]
  }>
  references?: string
}

export const PDFDocument: React.FC<PDFDocumentProps> = ({ title, authors, abstract, sections, references }) => (
  <Document>
    <Page size="A4" style={styles.page}>
      <View>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.authors}>{authors}</Text>

        {abstract && (
          <>
            <Text style={styles.abstractTitle}>Abstract</Text>
            <Text style={styles.abstract}>{abstract}</Text>
          </>
        )}

        {sections.map((section, index) => (
          <View key={index}>
            {section.title && <Text style={styles.sectionTitle}>{section.title}</Text>}
            {section.paragraphs.map((paragraph, pIndex) => (
              <Text key={pIndex} style={styles.paragraph}>
                {paragraph}
              </Text>
            ))}
          </View>
        ))}

        {references && (
          <>
            <Text style={styles.referencesTitle}>References</Text>
            {references.split("\n").map((reference, index) => (
              <Text key={index} style={styles.referenceItem}>
                {reference}
              </Text>
            ))}
          </>
        )}
      </View>

      <Text style={styles.pageNumber} render={({ pageNumber, totalPages }) => `${pageNumber} / ${totalPages}`} fixed />
    </Page>
  </Document>
)
