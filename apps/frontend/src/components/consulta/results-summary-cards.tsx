import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AdjudicationResult } from "@/types"

interface ResultsSummaryCardsProps {
  phenotype?: AdjudicationResult
  eoss?: AdjudicationResult
  bioAge?: AdjudicationResult
}

export function ResultsSummaryCards({ phenotype, eoss, bioAge }: ResultsSummaryCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {phenotype && (
        <Card className="border-primary/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Fenotipo Acosta</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-bold">{phenotype.calculated_value}</p>
            {phenotype.explanation && (
              <p className="text-xs text-muted-foreground mt-1">{phenotype.explanation}</p>
            )}
          </CardContent>
        </Card>
      )}
      {eoss && (
        <Card className="border-primary/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">EOSS Stage</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-bold">{eoss.calculated_value}</p>
            {eoss.explanation && (
              <p className="text-xs text-muted-foreground mt-1">{eoss.explanation}</p>
            )}
          </CardContent>
        </Card>
      )}
      {bioAge && (
        <Card className="border-primary/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Edad Biológica</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-bold">{bioAge.calculated_value}</p>
            {bioAge.explanation && (
              <p className="text-xs text-muted-foreground mt-1">{bioAge.explanation}</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
