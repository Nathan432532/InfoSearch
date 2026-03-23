import * as XLSX from "xlsx";
import type { CompanyResult } from "../pages/ResultPages/ResultPageCompany/CompanyResultPage";

export const downloadAsExcel = (
  data: CompanyResult[],
  filename = "report.xlsx",
) => {
  // 1. Transformeer de data naar een platte structuur (geschikt voor kolommen)
  const worksheetData = data.map((item) => ({
    ID: item.id,
    Bedrijf: item.bedrijfsnaam,
    Score: `${item.score}/10`,
    Locatie: item.locatie,
    Sector: item.sector,
    Techstack: item.techstack.join(", "),
    Contact: item.contactgegevens,
    Beschrijving: item.beschrijving,
    Waarom: item.waarom,
  }));

  // 2. Maak een nieuw werkblad en een 'workbook' aan
  const worksheet = XLSX.utils.json_to_sheet(worksheetData);

  const objectMaxLength: number[] = [];
  const keys = Object.keys(worksheetData[0]);

  worksheetData.forEach((row) => {
    keys.forEach((key, index) => {
      const value = row[key as keyof typeof row]
        ? row[key as keyof typeof row].toString()
        : "";
      const columnWidth = value.length;

      // Vergelijk huidige breedte met de vorige opgeslagen breedte
      objectMaxLength[index] = Math.max(
        objectMaxLength[index] || 10,
        columnWidth,
      );
    });
  });

  worksheet["!cols"] = objectMaxLength.map((w) => ({ wch: w + 2 }));

  // 4. Maak het workbook en sla op
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Data");
  XLSX.writeFile(workbook, filename);
};
