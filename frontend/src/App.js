import React, { useState } from "react";
import axios from "axios";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./components/ui/select";
import { Progress } from "./components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "./components/ui/alert";
import {
  Target,
  Building2,
  DollarSign,
  MapPin,
  Calendar,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  Loader2,
  Sparkles,
  Search,
  Link,
  Trash2,
} from "lucide-react";

function App() {
  const [companyData, setCompanyData] = useState({
    company_name: "",
    business_id: "",
    industry: "",
    employee_count: "",
    funding_need_amount: "",
    growth_stage: "growth",
    funding_purpose: "rdi",
    additional_info: "",
  });

  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [companyAnalysis, setCompanyAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [showAllResults, setShowAllResults] = useState(false);
  const [translatedDescriptions, setTranslatedDescriptions] = useState({});
  const [translatingIndex, setTranslatingIndex] = useState(null);
  const [clearingCache, setClearingCache] = useState(false);

  // Helper function to convert URLs in text to clickable links
  const renderTextWithLinks = (text) => {
    if (!text) return text;

    // URL regex pattern
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = text.split(urlRegex);

    return parts.map((part, index) => {
      if (part.match(urlRegex)) {
        return (
          <a
            key={index}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 underline font-medium"
          >
            {part}
          </a>
        );
      }
      return part;
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCompanyData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setAnalysisLoading(true);
    setError(null);
    setRecommendations([]);
    setCompanyAnalysis(null);

    try {
      const payload = {
        ...companyData,
        employee_count: companyData.employee_count
          ? parseInt(companyData.employee_count)
          : null,
        funding_need_amount: companyData.funding_need_amount
          ? parseInt(companyData.funding_need_amount)
          : null,
      };

      console.log("Sending request:", payload);

      // Start both requests in parallel
      const [analysisResponse, recommendationsResponse] = await Promise.all([
        axios.post("/api/generate-company-description", payload),
        axios.post("/api/analyze-company", payload),
      ]);

      setCompanyAnalysis(analysisResponse.data);
      setRecommendations(recommendationsResponse.data);
      setShowAllResults(false); // Reset to show only top 5
    } catch (err) {
      console.error("Error:", err);
      setError(
        err.response?.data?.detail ||
          "An error occurred while analyzing the company"
      );
    } finally {
      setLoading(false);
      setAnalysisLoading(false);
    }
  };

  const testCompanies = [
    {
      name: "Meyer Turku Oy",
      data: {
        company_name: "Meyer Turku Oy",
        business_id: "0772017-4",
        industry:
          "Finnish shipyard specializing in the design and construction of advanced cruise ships,",
        employee_count: "1961",
        funding_need_amount: "10000000",
        growth_stage: "scale-up",
        funding_purpose: "equipment",
        additional_info:
          "Major shipbuilding and ship repair company based in Turku, specializing in cruise ships and specialized vessels",
      },
    },
    {
      name: "Turku Science Park Oy",
      data: {
        company_name: "Turku Science Park Oy",
        business_id: "2322323-1",
        industry: "regional business development agency",
        employee_count: "60",
        funding_need_amount: "1500000",
        growth_stage: "growth",
        funding_purpose: "investments",
        additional_info:
          "Technology center providing innovation services and business development support in Turku",
      },
    },
    {
      name: "Kongsberg Maritime Finland OY",
      data: {
        company_name: "Kongsberg Maritime Finland OY",
        business_id: "1007628-7",
        industry: "Mechanical engineering and metalworking",
        employee_count: "14994",
        funding_need_amount: "3000000",
        growth_stage: "scale-up",
        funding_purpose: "rdi",
        additional_info:
          "Maritime technology and engineering solutions provider based in Rauma, Finland",
      },
    },
    {
      name: "Reaktor Advanced Technologies Oy",
      data: {
        company_name: "Reaktor Advanced Technologies Oy",
        business_id: "2535449-7",
        industry: "Computer programming activities",
        employee_count: "479",
        funding_need_amount: "1000000",
        growth_stage: "scale-up",
        funding_purpose: "internationalization",
        additional_info:
          "Software development and technology consulting services",
      },
    },
  ];

  const loadTestCompany = (testData) => {
    setCompanyData(testData);
  };

  const translateDescription = async (index, description, programName) => {
    if (translatedDescriptions[index]) {
      // Already translated, toggle back to original
      const newTranslations = { ...translatedDescriptions };
      delete newTranslations[index];
      setTranslatedDescriptions(newTranslations);
      return;
    }

    setTranslatingIndex(index);
    try {
      const response = await axios.post("/api/translate-description", {
        text: description,
      });

      setTranslatedDescriptions({
        ...translatedDescriptions,
        [index]: response.data.translated_text,
      });
    } catch (err) {
      console.error("Translation error:", err);
      setError("Failed to translate description");
    } finally {
      setTranslatingIndex(null);
    }
  };

  const isFinnishProgram = (source) => {
    return source === "ely" || source === "finnvera";
  };

  const handleClearCache = async () => {
    if (
      !window.confirm(
        "Are you sure you want to clear all cached results? This will force fresh queries for all companies."
      )
    ) {
      return;
    }

    setClearingCache(true);
    try {
      const response = await axios.delete("/api/clear-cache");
      alert(
        `✓ Cache cleared successfully! Cleared ${response.data.cleared_count} cached files.`
      );
    } catch (err) {
      console.error("Error clearing cache:", err);
      alert("Failed to clear cache. Please try again.");
    } finally {
      setClearingCache(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
        <div className="container mx-auto px-4 py-8 text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Target className="h-12 w-12" />
            <h1 className="text-4xl font-bold">Smart Funding Advisor</h1>
          </div>
          <p className="text-xl text-blue-100">
            AI-powered funding matchmaking for Finnish companies
          </p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Test Companies */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="h-5 w-5" />
                  Quick Test Companies
                </CardTitle>
                <CardDescription>
                  Try our demo with these sample companies
                </CardDescription>
              </div>
              <Button
                onClick={handleClearCache}
                disabled={clearingCache}
                variant="outline"
                size="sm"
                className="flex items-center gap-2 text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                {clearingCache ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Clearing...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4" />
                    Clear Cache
                  </>
                )}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              {testCompanies.map((test, index) => (
                <Button
                  key={index}
                  onClick={() => loadTestCompany(test.data)}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Building2 className="h-4 w-4" />
                  {test.name}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Company Form */}
        <Card>
          <CardHeader>
            <CardTitle>Company Information</CardTitle>
            <CardDescription>
              Enter your company details to discover funding opportunities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid gap-6">
                {/* Company Name */}
                <div className="space-y-2">
                  <Label htmlFor="company_name">Company Name *</Label>
                  <Input
                    id="company_name"
                    name="company_name"
                    value={companyData.company_name}
                    onChange={handleInputChange}
                    required
                  />
                </div>

                {/* Business ID and Employee Count */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="business_id">
                      Business ID (Y-tunnus) *
                    </Label>
                    <Input
                      id="business_id"
                      name="business_id"
                      value={companyData.business_id}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="employee_count">
                      Number of Employees *
                    </Label>
                    <Input
                      id="employee_count"
                      name="employee_count"
                      type="number"
                      value={companyData.employee_count}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </div>

                {/* Industry Description */}
                <div className="space-y-2">
                  <Label htmlFor="industry">Industry Description *</Label>
                  <Input
                    id="industry"
                    name="industry"
                    value={companyData.industry}
                    onChange={handleInputChange}
                    required
                  />
                </div>

                {/* Funding Need and Growth Stage */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="funding_need_amount">
                      Funding Need (EUR) *
                    </Label>
                    <Input
                      id="funding_need_amount"
                      name="funding_need_amount"
                      type="number"
                      value={companyData.funding_need_amount}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="growth_stage">Growth Stage *</Label>
                    <Select
                      value={companyData.growth_stage}
                      onValueChange={(value) =>
                        setCompanyData((prev) => ({
                          ...prev,
                          growth_stage: value,
                        }))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pre-seed">Pre-seed</SelectItem>
                        <SelectItem value="seed">Seed</SelectItem>
                        <SelectItem value="growth">Growth</SelectItem>
                        <SelectItem value="scale-up">Scale-up</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Funding Purpose */}
                <div className="space-y-2">
                  <Label htmlFor="funding_purpose">Funding Purpose *</Label>
                  <Select
                    value={companyData.funding_purpose}
                    onValueChange={(value) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        funding_purpose: value,
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="rdi">
                        Research & Development
                      </SelectItem>
                      <SelectItem value="internationalization">
                        Internationalization
                      </SelectItem>
                      <SelectItem value="investments">Investments</SelectItem>
                      <SelectItem value="equipment">Equipment</SelectItem>
                      <SelectItem value="working_capital">
                        Working Capital
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Additional Information */}
                <div className="space-y-2">
                  <Label htmlFor="additional_info">
                    Additional Information
                  </Label>
                  <Textarea
                    id="additional_info"
                    name="additional_info"
                    value={companyData.additional_info}
                    onChange={handleInputChange}
                    rows={3}
                    placeholder="Any additional context about your company or funding needs..."
                  />
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full h-12"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Target className="mr-2 h-4 w-4" />
                      Find Funding Opportunities
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Loading State */}
        {loading && (
          <Card>
            <CardContent className="py-8">
              <div className="text-center space-y-4">
                <div className="loading-spinner mx-auto"></div>
                <h3 className="text-lg font-semibold">
                  Analyzing Your Company
                </h3>
                <p className="text-muted-foreground">
                  Discovering funding opportunities and calculating matches...
                </p>
                <p className="text-sm text-muted-foreground">
                  This may take 10-15 seconds
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Error State */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Company Analysis */}
        {companyAnalysis && (
          <Card className="bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-purple-800">
                <Sparkles className="h-5 w-5" />
                AI Company Analysis
              </CardTitle>
              <CardDescription className="text-purple-600">
                Generated insights for {companyAnalysis.company_name}
                {companyAnalysis.ai_confidence && (
                  <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                    {companyAnalysis.ai_confidence} confidence
                  </span>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Company Website Link */}
              {companyAnalysis.company_website && (
                <div className="flex items-center gap-2 mb-4">
                  <Link className="h-4 w-4 text-blue-600" />
                  <a
                    href={companyAnalysis.company_website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 underline font-medium"
                  >
                    {companyAnalysis.company_website}
                  </a>
                </div>
              )}

              {/* Company Description */}
              <div className="space-y-3">
                <h4 className="font-semibold text-purple-800 flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  Company Overview
                </h4>
                <p className="text-gray-700 leading-relaxed">
                  {companyAnalysis.company_description}
                </p>
              </div>

              {/* Hashtags */}
              {companyAnalysis.hashtags &&
                companyAnalysis.hashtags.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex flex-wrap gap-2">
                      {companyAnalysis.hashtags.map((hashtag, index) => (
                        <span
                          key={index}
                          className="bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded-full font-medium"
                        >
                          {hashtag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

              {/* Citations (if available) */}
              {companyAnalysis.citations &&
                companyAnalysis.citations.length > 0 && (
                  <div className="space-y-2 border-t border-purple-200 pt-4">
                    <h4 className="font-semibold text-gray-700 flex items-center gap-2 text-sm">
                      <Search className="h-3 w-3" />
                      Research Sources ({companyAnalysis.citations.length})
                    </h4>
                    <div className="text-xs text-gray-500 space-y-1">
                      {companyAnalysis.citations
                        .slice(0, 3)
                        .map((citation, index) => (
                          <div key={index} className="flex items-center gap-2">
                            <Link className="h-3 w-3" />
                            <a
                              href={citation}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 underline truncate"
                            >
                              {citation}
                            </a>
                          </div>
                        ))}
                      {companyAnalysis.citations.length > 3 && (
                        <p className="text-gray-400 text-xs">
                          +{companyAnalysis.citations.length - 3} more sources
                        </p>
                      )}
                    </div>
                  </div>
                )}
            </CardContent>
          </Card>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Funding Recommendations
                </CardTitle>
                <CardDescription>
                  Found {recommendations.length} suitable funding opportunities
                  for your company
                  {recommendations.length > 5 && !showAllResults && (
                    <span className="ml-1 text-muted-foreground">
                      (showing top 5)
                    </span>
                  )}
                </CardDescription>
              </CardHeader>
            </Card>

            {(showAllResults
              ? recommendations
              : recommendations.slice(0, 5)
            ).map((rec, index) => (
              <Card key={index} className="overflow-hidden">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-xl">
                        {rec.program.program_name}
                      </CardTitle>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <MapPin className="h-4 w-4" />
                        {rec.program.source.replace("_", " ").toUpperCase()}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {Math.round(rec.match_score.total_score * 100)}%
                      </div>
                      <div className="text-xs text-muted-foreground">Match</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <CardDescription>
                      {translatedDescriptions[index] || rec.program.description}
                    </CardDescription>
                    {isFinnishProgram(rec.program.source) && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          translateDescription(
                            index,
                            rec.program.description,
                            rec.program.program_name
                          )
                        }
                        disabled={translatingIndex === index}
                        className="text-xs text-blue-600 hover:text-blue-800"
                      >
                        {translatingIndex === index ? (
                          <>
                            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                            Translating...
                          </>
                        ) : translatedDescriptions[index] ? (
                          "Show Original Finnish"
                        ) : (
                          "Translate to English"
                        )}
                      </Button>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="space-y-6">
                  {/* Funding Details */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-muted rounded-lg">
                    <div className="flex items-center gap-2">
                      <DollarSign className="h-4 w-4 text-green-600" />
                      <div>
                        <div className="text-sm font-medium">Funding Range</div>
                        <div className="text-xs text-muted-foreground">
                          €{rec.program.min_funding?.toLocaleString()} - €
                          {rec.program.max_funding?.toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-blue-600" />
                      <div>
                        <div className="text-sm font-medium">Type</div>
                        <div className="text-xs text-muted-foreground capitalize">
                          {rec.program.funding_type}
                        </div>
                      </div>
                    </div>
                    {rec.program.application_deadline && (
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-orange-600" />
                        <div>
                          <div className="text-sm font-medium">Deadline</div>
                          <div className="text-xs text-muted-foreground">
                            {rec.program.application_deadline}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Match Breakdown */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold">Match Breakdown</h4>
                    <div className="space-y-2">
                      {[
                        {
                          label: "Industry (30%)",
                          score: rec.match_score.industry_score,
                          weight: 0.3,
                        },
                        {
                          label: "Geography (25%)",
                          score: rec.match_score.geography_score,
                          weight: 0.25,
                        },
                        {
                          label: "Size (20%)",
                          score: rec.match_score.size_score,
                          weight: 0.2,
                        },
                        {
                          label: "Amount (15%)",
                          score: rec.match_score.funding_score,
                          weight: 0.15,
                        },
                        {
                          label: "Timing (10%)",
                          score: rec.match_score.deadline_score,
                          weight: 0.1,
                        },
                      ].map((item) => (
                        <div
                          key={item.label}
                          className="flex items-center gap-3"
                        >
                          <div className="text-sm font-medium w-32">
                            {item.label}:
                          </div>
                          <Progress
                            value={item.score * 100}
                            className="flex-1"
                          />
                          <div className="text-sm font-medium w-16 text-right">
                            {Math.round(item.score * 100)}%
                          </div>
                          <div className="text-xs text-gray-500 w-12 text-right">
                            +{Math.round(item.score * item.weight * 100)}%
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Justification */}
                  <Alert>
                    <CheckCircle2 className="h-4 w-4" />
                    <AlertTitle>Why this matches</AlertTitle>
                    <AlertDescription>
                      <ul className="space-y-1 mt-2">
                        {rec.justification.map((point, pointIndex) => (
                          <li
                            key={pointIndex}
                            className="text-sm flex items-start gap-2"
                          >
                            <div className="text-green-500 mt-1">•</div>
                            <span>{point}</span>
                          </li>
                        ))}
                      </ul>
                    </AlertDescription>
                  </Alert>

                  {/* Next Steps */}
                  {rec.next_steps.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-semibold flex items-center gap-2">
                        <ArrowRight className="h-4 w-4" />
                        Next Steps
                      </h4>
                      <ul className="space-y-2">
                        {rec.next_steps.map((step, stepIndex) => (
                          <li
                            key={stepIndex}
                            className="text-sm flex items-start gap-2"
                          >
                            <div className="text-primary mt-1">•</div>
                            <span>{renderTextWithLinks(step)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Warnings */}
                  {rec.warnings.length > 0 && (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertTitle>Important Notes</AlertTitle>
                      <AlertDescription>
                        <ul className="space-y-1 mt-2">
                          {rec.warnings.map((warning, warnIndex) => (
                            <li
                              key={warnIndex}
                              className="text-sm flex items-start gap-2"
                            >
                              <div className="text-orange-500 mt-1">•</div>
                              <span>{warning}</span>
                            </li>
                          ))}
                        </ul>
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            ))}

            {/* Show More / Show Less Button */}
            {recommendations.length > 5 && (
              <div className="flex justify-center">
                <Button
                  onClick={() => setShowAllResults(!showAllResults)}
                  variant="outline"
                  className="w-full md:w-auto"
                >
                  {showAllResults ? (
                    <>
                      Show Less
                      <ArrowRight className="ml-2 h-4 w-4 rotate-90" />
                    </>
                  ) : (
                    <>
                      Show More ({recommendations.length - 5} more programs)
                      <ArrowRight className="ml-2 h-4 w-4 -rotate-90" />
                    </>
                  )}
                </Button>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t bg-white py-8 mt-16">
        <div className="container mx-auto px-4 text-center">
          <p className="text-muted-foreground">
            SinceAI Hackathon 2025 - Smart Funding Advisor MVP
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
