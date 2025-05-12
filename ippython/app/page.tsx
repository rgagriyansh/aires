import { FormattingTool } from "@/components/formatting-tool"

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">IPPython</h1>
          <p className="text-xl text-gray-600">Transform plain text into professionally formatted research papers</p>
        </div>

        <FormattingTool />

        <footer className="mt-16 text-center text-gray-500 text-sm">
          <p>© {new Date().getFullYear()} IPPython. All rights reserved.</p>
        </footer>
      </div>
    </main>
  )
}
