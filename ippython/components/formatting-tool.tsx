"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { PDFDocument } from "@/components/pdf-document"
import { PDFDownloadLink } from "@react-pdf/renderer"
import { Loader2, FileDown, Eye, FileText } from "lucide-react"
import { formatPaper } from "@/lib/format-paper"

export function FormattingTool() {
  const [paperData, setPaperData] = useState({
    title: "",
    authors: "",
    abstract: "",
    content: "",
    references: "",
  })

  const [formattedSections, setFormattedSections] = useState<any>(null)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setPaperData((prev) => ({ ...prev, [name]: value }))
  }

  const handleFormatPaper = () => {
    const formatted = formatPaper(paperData.content)
    setFormattedSections(formatted)
  }

  const isFormValid =
    paperData.title.trim() !== "" && paperData.authors.trim() !== "" && paperData.content.trim() !== ""

  return (
    <div className="space-y-8">
      <Tabs defaultValue="input" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="input" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Input
          </TabsTrigger>
          <TabsTrigger value="preview" className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Preview
          </TabsTrigger>
          <TabsTrigger value="download" className="flex items-center gap-2">
            <FileDown className="h-4 w-4" />
            Download
          </TabsTrigger>
        </TabsList>

        <TabsContent value="input">
          <Card>
            <CardContent className="pt-6 space-y-6">
              <div className="space-y-2">
                <Label htmlFor="title">Paper Title</Label>
                <Input
                  id="title"
                  name="title"
                  placeholder="Enter the title of your paper"
                  value={paperData.title}
                  onChange={handleInputChange}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="authors">Authors</Label>
                <Input
                  id="authors"
                  name="authors"
                  placeholder="Author names (separated by commas)"
                  value={paperData.authors}
                  onChange={handleInputChange}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="abstract">Abstract (Optional)</Label>
                <Textarea
                  id="abstract"
                  name="abstract"
                  placeholder="Enter the abstract of your paper"
                  value={paperData.abstract}
                  onChange={handleInputChange}
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="content">Paper Content</Label>
                <Textarea
                  id="content"
                  name="content"
                  placeholder="Paste your paper content here"
                  value={paperData.content}
                  onChange={handleInputChange}
                  rows={10}
                  className="font-mono text-sm"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="references">References (Optional)</Label>
                <Textarea
                  id="references"
                  name="references"
                  placeholder="Enter your references"
                  value={paperData.references}
                  onChange={handleInputChange}
                  rows={3}
                />
              </div>

              <Button onClick={handleFormatPaper} disabled={!isFormValid} className="w-full">
                Format Paper
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preview">
          <Card className="min-h-[500px]">
            <CardContent className="pt-6">
              {formattedSections ? (
                <div className="border rounded-md p-6 bg-white">
                  <div className="text-center mb-8">
                    <h1 className="text-2xl font-bold mb-4">{paperData.title}</h1>
                    <p className="text-gray-700">{paperData.authors}</p>
                  </div>

                  {paperData.abstract && (
                    <div className="mb-6">
                      <h2 className="text-xl font-semibold mb-2">Abstract</h2>
                      <p className="text-gray-800">{paperData.abstract}</p>
                    </div>
                  )}

                  {formattedSections.map((section: any, index: number) => (
                    <div key={index} className="mb-6">
                      {section.title && <h2 className="text-xl font-semibold mb-2">{section.title}</h2>}
                      <div className="space-y-2">
                        {section.paragraphs.map((paragraph: string, pIndex: number) => (
                          <p key={pIndex} className="text-gray-800">
                            {paragraph}
                          </p>
                        ))}
                      </div>
                    </div>
                  ))}

                  {paperData.references && (
                    <div className="mt-8">
                      <h2 className="text-xl font-semibold mb-2">References</h2>
                      <div className="text-gray-800 space-y-2">
                        {paperData.references.split("\n").map((ref, index) => (
                          <p key={index}>{ref}</p>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-[500px] text-gray-500">
                  <FileText className="h-16 w-16 mb-4 opacity-30" />
                  <p>Format your paper to see a preview</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="download">
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center justify-center py-12">
                {formattedSections ? (
                  <div className="text-center">
                    <PDFDownloadLink
                      document={
                        <PDFDocument
                          title={paperData.title}
                          authors={paperData.authors}
                          abstract={paperData.abstract}
                          sections={formattedSections}
                          references={paperData.references}
                        />
                      }
                      fileName={`${paperData.title.replace(/\s+/g, "_")}.pdf`}
                      className="inline-block"
                    >
                      {({ loading }) => (
                        <Button size="lg" className="gap-2">
                          {loading ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin" />
                              Preparing PDF...
                            </>
                          ) : (
                            <>
                              <FileDown className="h-4 w-4" />
                              Download PDF
                            </>
                          )}
                        </Button>
                      )}
                    </PDFDownloadLink>
                    <p className="mt-4 text-gray-500 text-sm">Your formatted research paper is ready to download</p>
                  </div>
                ) : (
                  <div className="text-center">
                    <FileDown className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                    <h3 className="text-lg font-medium mb-2">No Document Ready</h3>
                    <p className="text-gray-500 mb-6">Format your paper first to generate a downloadable PDF</p>
                    <Button
                      variant="outline"
                      onClick={() => document.querySelector('[value="input"]')?.dispatchEvent(new Event("click"))}
                    >
                      Go to Input
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="bg-amber-50 border border-amber-200 rounded-md p-4">
        <h3 className="font-medium text-amber-800 mb-2">How to use IPPython</h3>
        <ol className="list-decimal list-inside text-amber-700 space-y-1">
          <li>Enter your paper title and author information</li>
          <li>Paste your paper content in the content field</li>
          <li>Click "Format Paper" to process your document</li>
          <li>Preview the formatted paper in the Preview tab</li>
          <li>Download your professionally formatted PDF</li>
        </ol>
      </div>
    </div>
  )
}
