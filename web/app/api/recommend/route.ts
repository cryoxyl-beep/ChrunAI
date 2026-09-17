import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextResponse } from "next/server";
import type { RecommendRequestBody, RetentionAction, ScoredCustomer } from "@/lib/types";

function buildPrompt(
  customer: ScoredCustomer,
  probability: number,
  tier: string,
  actions: RetentionAction[]
): string {
  const rulesText = actions
    .map((a) => `- [${a.priority}] ${a.action} (${a.rationale})`)
    .join("\n");
  const customerSummary =
    `customerID=${customer.customerID}, Contract=${customer.Contract}, ` +
    `tenure=${customer.tenure}, PaymentMethod=${customer.PaymentMethod}, ` +
    `InternetService=${customer.InternetService}, ` +
    `MonthlyCharges=${customer.MonthlyCharges}`;

  return `You are a telco customer retention analyst. Write a short, actionable retention plan (4-6 bullet points) for this at-risk customer.

Use ONLY these facts (do not invent data):
- Churn probability: ${(probability * 100).toFixed(1)}%
- Risk tier: ${tier}
- Customer: ${customerSummary}
- Rule-based actions already identified:
${rulesText}

Tone: professional, specific, suitable for a CRM note. Mention probability and tier once.`;
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as RecommendRequestBody;
    const { customer, actions } = body;
    if (!customer?.customerID || !actions?.length) {
      return NextResponse.json(
        { error: "Invalid request body" },
        { status: 400 }
      );
    }

    const key = process.env.GEMINI_API_KEY;
    if (!key) {
      return NextResponse.json(
        { error: "GEMINI_API_KEY not set in web/.env.local" },
        { status: 503 }
      );
    }

    const genAI = new GoogleGenerativeAI(key);
    const model = genAI.getGenerativeModel({ model: "gemini-3.6-flash" });
    const prompt = buildPrompt(
      customer,
      customer.churn_probability,
      customer.risk_tier,
      actions
    );
    const result = await model.generateContent(prompt);
    const text = result.response.text().trim();

    return NextResponse.json({ text });
  } catch (e) {
    const message =
      e instanceof Error ? e.message : "Gemini request failed";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
