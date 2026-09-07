Attribute VB_Name = "ResearchPipelineIntegration"
' ============================================================================
' Research Pipeline Integration Macro
'
' Purpose: import the Python/R pipeline's CSV exports (exports/asu_standards.csv,
' exports/firm_adoptions.csv, exports/standard_impact_metrics.csv) into an
' Excel workbook and build a compliance-summary pivot-ready table, so
' researchers who work primarily in Excel can consume pipeline output
' without touching Python, SQL, or R directly.
'
' Usage:
'   1. Open a blank workbook, Alt+F11, import this module (File > Import File).
'   2. Set EXPORTS_FOLDER below to the project's exports/ directory.
'   3. Run RefreshResearchPipelineData (Developer > Macros, or F5 with cursor
'      inside the sub).
' ============================================================================
Option Explicit

Private Const EXPORTS_FOLDER As String = "C:\path\to\accounting-regulation-impact-system\exports\"

Public Sub RefreshResearchPipelineData()
    Dim wb As Workbook
    Set wb = ThisWorkbook

    ImportCsvToSheet wb, EXPORTS_FOLDER & "asu_standards.csv", "ASU_Standards"
    ImportCsvToSheet wb, EXPORTS_FOLDER & "firm_adoptions.csv", "Firm_Adoptions"
    ImportCsvToSheet wb, EXPORTS_FOLDER & "standard_impact_metrics.csv", "Impact_Metrics"

    BuildComplianceSummary wb
    MsgBox "Research pipeline data refreshed: " & Now(), vbInformation
End Sub

Private Sub ImportCsvToSheet(wb As Workbook, csvPath As String, sheetName As String)
    Dim ws As Worksheet

    If Dir(csvPath) = "" Then
        MsgBox "Missing export file: " & csvPath & vbCrLf & _
               "Run 'python -m src.pipeline' first to generate it.", vbExclamation
        Exit Sub
    End If

    On Error Resume Next
    Application.DisplayAlerts = False
    wb.Worksheets(sheetName).Delete
    Application.DisplayAlerts = True
    On Error GoTo 0

    Set ws = wb.Worksheets.Add(After:=wb.Worksheets(wb.Worksheets.Count))
    ws.Name = sheetName

    With ws.QueryTables.Add(Connection:="TEXT;" & csvPath, Destination:=ws.Range("A1"))
        .TextFileParseType = xlDelimited
        .TextFileCommaDelimiter = True
        .TextFileConsecutiveDelimiter = False
        .Refresh BackgroundQuery:=False
    End With

    ws.ListObjects.Add(xlSrcRange, ws.UsedRange, , xlYes).Name = "tbl_" & sheetName
    ws.Columns.AutoFit
End Sub

' Builds a research-facing summary: for each standard, deliberation lag,
' issuance-to-effective lag, adoption mix, and restatement rate side by side —
' the table a research assistant would hand to a PI or drop into a working paper.
Private Sub BuildComplianceSummary(wb As Workbook)
    Dim standardsWs As Worksheet, metricsWs As Worksheet, summaryWs As Worksheet
    Dim lastRowStandards As Long, lastRowMetrics As Long
    Dim i As Long, matchRow As Long
    Dim asuNumber As String

    On Error Resume Next
    Set standardsWs = wb.Worksheets("ASU_Standards")
    Set metricsWs = wb.Worksheets("Impact_Metrics")
    On Error GoTo 0
    If standardsWs Is Nothing Or metricsWs Is Nothing Then Exit Sub

    On Error Resume Next
    Application.DisplayAlerts = False
    wb.Worksheets("Compliance_Summary").Delete
    Application.DisplayAlerts = True
    On Error GoTo 0

    Set summaryWs = wb.Worksheets.Add(After:=wb.Worksheets(wb.Worksheets.Count))
    summaryWs.Name = "Compliance_Summary"

    Dim headers As Variant
    headers = Array("ASU Number", "Topic Code", "Title", "Deliberation Lag (days)", _
                     "Issuance-to-Effective (days)", "Firms Tracked", "Early Adopters", _
                     "On-Time Adopters", "Late Adopters", "Restatement Rate", "Avg Audit Fee (USD)")
    For i = 0 To UBound(headers)
        summaryWs.Cells(1, i + 1).Value = headers(i)
    Next i
    summaryWs.Rows(1).Font.Bold = True

    lastRowStandards = standardsWs.Cells(standardsWs.Rows.Count, "A").End(xlUp).Row
    lastRowMetrics = metricsWs.Cells(metricsWs.Rows.Count, "A").End(xlUp).Row

    Dim outRow As Long
    outRow = 2
    For i = 2 To lastRowStandards
        asuNumber = standardsWs.Cells(i, 1).Value
        matchRow = FindRowByKey(metricsWs, asuNumber, lastRowMetrics)
        If matchRow > 0 Then
            summaryWs.Cells(outRow, 1).Value = asuNumber
            summaryWs.Cells(outRow, 2).Value = standardsWs.Cells(i, 2).Value  ' topic_code
            summaryWs.Cells(outRow, 3).Value = standardsWs.Cells(i, 3).Value  ' title
            summaryWs.Cells(outRow, 4).Value = metricsWs.Cells(matchRow, 2).Value  ' deliberation_lag_days
            summaryWs.Cells(outRow, 5).Value = metricsWs.Cells(matchRow, 3).Value  ' issuance_to_effective_days
            summaryWs.Cells(outRow, 6).Value = metricsWs.Cells(matchRow, 4).Value  ' n_firms_tracked
            summaryWs.Cells(outRow, 7).Value = metricsWs.Cells(matchRow, 5).Value  ' n_early_adopters
            summaryWs.Cells(outRow, 8).Value = metricsWs.Cells(matchRow, 6).Value  ' n_on_time_adopters
            summaryWs.Cells(outRow, 9).Value = metricsWs.Cells(matchRow, 7).Value  ' n_late_adopters
            summaryWs.Cells(outRow, 10).Value = metricsWs.Cells(matchRow, 8).Value ' restatement_rate
            summaryWs.Cells(outRow, 11).Value = metricsWs.Cells(matchRow, 9).Value ' avg_audit_fee_usd
            outRow = outRow + 1
        End If
    Next i

    summaryWs.Range("J2:J" & outRow - 1).NumberFormat = "0.0%"
    summaryWs.Range("K2:K" & outRow - 1).NumberFormat = "#,##0"
    summaryWs.Columns.AutoFit
    summaryWs.ListObjects.Add(xlSrcRange, summaryWs.Range("A1:K" & outRow - 1), , xlYes).Name = "tbl_ComplianceSummary"
End Sub

Private Function FindRowByKey(ws As Worksheet, key As String, lastRow As Long) As Long
    Dim r As Long
    For r = 2 To lastRow
        If ws.Cells(r, 1).Value = key Then
            FindRowByKey = r
            Exit Function
        End If
    Next r
    FindRowByKey = 0
End Function
