Const ShiftUpDownPlan = 0
Const ShiftUpDownSide = 1
Const ShiftUpDownFront = 2
Const ShiftLeftRightPlan = 3
Const ShiftLeftRightSide = 4
Const ShiftLeftRightFront = 5
Const RotateAnglePlan = 6
Const RotateAngleSide = 7
Const RotateAngleFront = 8
Const WriteData = 9
Const ResetData = 10

Const PosX = 0
Const PosY = 1
Const PosZ = 2
Const PW = 3

' Added by Shannon for 3D rotation
Private Type Point
    X As Single
    Y As Single
    z As Single
End Type
' end added by Shannon

Dim Cancelling As Boolean
Dim DataChanged As Boolean
'For the following three cum variables, 0 = plan, 1=side, 2=front
Dim CumAngle(3) As Single
Dim CumUpDown(3) As Single
Dim CumLeftRight(3) As Single

Dim SmallDatum As Boolean
Dim CurrentRotationName As String

Dim Shift As Single
Dim ViewIndex As Integer
Dim Sign As Integer
Dim OptionScale As Integer
Dim OptionButton As Object

Dim Xorigin As Single
Dim Yorigin As Single
Dim Zorigin As Single

Dim Recording As Boolean
Dim rstRecording As Recordset
Dim PlotShiftRotate As Boolean
Dim PreviousAction As Integer
Dim CurrentAction As Integer
Dim TempShift As Single
Dim FindOrigin As Boolean
Dim Xmin As Single
Dim XMax As Single
Dim Ymin As Single
Dim YMax As Single
Dim Zmin As Single
Dim ZMax As Single


Private Sub cmdDeleteRotation_Click()

Dim tempstring As String
tempstring = "RSR_" & lstRotations.List(lstRotations.ListIndex)
MDImain.MainDB.TableDefs.Delete tempstring
GetRotations
cmdDeleteRotation.Enabled = False

End Sub


Private Sub cmdApplyRotation_Click()

Dim tempstring As String

Screen.MousePointer = 11
PlotShiftRotate = False
For i = 0 To 5
    cmdUpDown(i).Enabled = False
    cmdLeftRight(i).Enabled = False
    cmdRotate(i).Enabled = False
Next i

optUpDown(0) = True
optUpDown(3) = True
optUpDown(6) = True
optLeftRight(0) = True
optLeftRight(3) = True
optLeftRight(6) = True

tempstring = "RSR_" & lstRotations.List(lstRotations.ListIndex)

Set rstRecording = MDImain.MainDB.OpenRecordset(tempstring, dbOpenTable)
rstRecording.Index = "Step"
rstRecording.MoveFirst
While Not rstRecording.EOF
'    Select Case rstRecording("action")
'        Case 0, 3, 6
'            MDImain.ViewDirect_Click 0
'        Case 1, 4, 7
'            MDImain.ViewDirect_Click 1
'        Case 2, 5, 8
'            MDImain.ViewDirect_Click 2
'    End Select

    Shift = rstRecording("shift")
    Select Case rstRecording("action")
        Case 0
            txtUpDown(0) = Abs(Shift)
            If Shift >= 0 Then
                cmdUpDown_Click (0)
            Else
                cmdUpDown_Click (1)
            End If
        Case 1
            txtUpDown(1) = Abs(Shift)
            If Shift >= 0 Then
                cmdUpDown_Click (2)
            Else
                cmdUpDown_Click (3)
            End If

        Case 2
            txtUpDown(2) = Abs(Shift)
            If Shift >= 0 Then
                cmdUpDown_Click (4)
            Else
                cmdUpDown_Click (5)
            End If
        Case 3
            txtLeftRight(0) = Abs(Shift)
            If Shift >= 0 Then
                cmdLeftRight_Click (1)
            Else
                cmdLeftRight_Click (0)
            End If
        Case 4
            txtLeftRight(1) = Abs(Shift)
            If Shift >= 0 Then
                cmdLeftRight_Click (3)
            Else
                cmdLeftRight_Click (2)
            End If
        Case 5
            txtLeftRight(2) = Abs(Shift)
            If Shift >= 0 Then
                cmdLeftRight_Click (5)
            Else
                cmdLeftRight_Click (4)
            End If
        Case 6
            txtAngle(0) = Abs(Shift)
            If Shift >= 0 Then
                cmdRotate_Click (1)
            Else
                cmdRotate_Click (0)
            End If
        Case 7
            txtAngle(1) = Abs(Shift)
            If Shift >= 0 Then
                cmdRotate_Click (3)
            Else
                cmdRotate_Click (2)
            End If
        Case 8
            txtAngle(2) = Abs(Shift)
            If Shift >= 0 Then
                cmdRotate_Click (5)
            Else
                cmdRotate_Click (4)
            End If
    End Select
    
    rstRecording.MoveNext
'    xtimer = Timer
'    Do While Timer - xtimer < 0.5
'    Loop
    
Wend

CurrentPF.Cls
CurrentPF.Form_Paint
Select Case PlotView
    Case "XY"
        SetDirection 0
    Case "YZ"
        SetDirection 1
    Case "XZ"
        SetDirection 2
End Select

Screen.MousePointer = 1
PlotShiftRotate = True

End Sub

Private Sub cmdLeftRight_Click(Index As Integer)

Set OptionButton = optLeftRight
GetIndices Index
If Not IsNumeric(txtLeftRight(ViewIndex)) Then
    MsgBox ("Invalid (non-numeric characters) value for shift")
    Exit Sub
End If

Select Case Index
    Case 0, 2, 4
        Sign = -1
    Case Else
        Sign = 1
End Select

Shift = Val(txtLeftRight(ViewIndex)) / OptionScale * Sign
CumLeftRight(ViewIndex) = CumLeftRight(ViewIndex) + Shift
lblLeftRight(ViewIndex).Caption = Format(CumLeftRight(ViewIndex), "####0.000")
Select Case Index
    Case 0, 1
        MDImain.ShifTurn ShiftLeftRightPlan, Shift, 0, 0, PlotShiftRotate
        CurrentAction = ShiftLeftRightPlan
    Case 2, 3
        MDImain.ShifTurn ShiftLeftRightSide, Shift, 0, 0, PlotShiftRotate
        CurrentAction = ShiftLeftRightSide
    Case 4, 5
        MDImain.ShifTurn ShiftLeftRightFront, Shift, 0, 0, PlotShiftRotate
        CurrentAction = ShiftLeftRightFront
End Select
If Recording Then
    If CurrentAction = PreviousAction Then
        rstRecording.MoveLast
        TempShift = rstRecording("Shift")
        rstRecording.Edit
        rstRecording("Shift") = TempShift + Shift
        rstRecording.Update
    Else
        rstRecording.AddNew
        Select Case Index
            Case 0, 1
                rstRecording("action") = ShiftLeftRightPlan
                rstRecording("Shift") = Shift
                PreviousAction = ShiftLeftRightPlan
            Case 2, 3
                rstRecording("action") = ShiftLeftRightSide
                rstRecording("shift") = Shift
                PreviousAction = ShiftLeftRightSide
            Case 4, 5
                rstRecording("action") = ShiftLeftRightFront
                rstRecording("shift") = Shift
                PreviousAction = ShiftLeftRightFront
        End Select
        rstRecording.Update
    End If
End If

FindOrigin = True
DataChanged = True
Set OptionButton = Nothing

End Sub

Private Sub cmdRecord_Click()

If Recording = True Then
    Label12.Visible = False
    Recording = False
    Set rstRecording = Nothing
    cmdRecord.Caption = "Record Rotatation"
    If Not Cancelling Then
        lstRotations.AddItem Mid(CurrentRotationName, 5)
    End If
    Exit Sub
End If

Dim tempstring As String
Dim gotit As Boolean

Cancelling = False
MDImain.MainDB.TableDefs.Refresh

gotit = False
CurrentRotationName = InputBox("Enter name of Shift-Rotate", "Shift-Rotate Recording")
If CurrentRotationName = "" Then Exit Sub
For i = 0 To lstRotations.ListCount - 1
    If UCase(CurrentRotationName) = UCase(lstRotations.List(i)) Then
        response = MsgBox("Duplicate Shift-Rotate name.  Overwrite?", vbYesNoCancel)
        If response = vbCancel Or response = vbNo Then
            Exit Sub
        Else
            CurrentRotationName = "RSR_" & CurrentRotationName
            sqlString = "Delete [" & CurrentRotationName & "].* from [" & CurrentRotationName & "]"
            MDImain.MainDB.Execute sqlString
            gotit = True
        End If
        Exit For
    End If
Next i

If Not gotit Then
    CreateShiftRotateTable CurrentRotationName
End If

Set rstRecording = MDImain.MainDB.OpenRecordset(CurrentRotationName, dbOpenTable)
Label12.Visible = True
cmdRecord.Caption = "Stop Recording"
PreviousAction = -1
Recording = True

End Sub

Private Sub cmdRotate_Click(Index As Integer)

Select Case Index
    Case 0, 2, 4
        Sign = -1
    Case Else
        Sign = 1
End Select
Select Case Index
    Case 0, 1
        If Not IsNumeric(txtAngle(0)) Then
            MsgBox ("Invalid (non-numeric characters) value for rotate")
            Exit Sub
        End If
        Shift = Val(txtAngle(0)) * Sign
    Case 2, 3
        If Not IsNumeric(txtAngle(1)) Then
            MsgBox ("Invalid (non-numeric characters) value for rotate")
            Exit Sub
        End If
        Shift = Val(txtAngle(1)) * Sign
    Case 4, 5
        If Not IsNumeric(txtAngle(2)) Then
            MsgBox ("Invalid (non-numeric characters) value for rotate")
            Exit Sub
        End If
        Shift = Val(txtAngle(2)) * Sign
End Select

If FindOrigin Then
    Xmin = 32000
    XMax = -32000
    Ymin = 32000
    YMax = -32000
    Zmin = 32000
    ZMax = -32000
    For i = 1 To WBRecordCount
        If PlotPoints(1, i) > XMax Then XMax = PlotPoints(1, i)
        If PlotPoints(1, i) < Xmin Then Xmin = PlotPoints(1, i)
        If PlotPoints(2, i) > YMax Then YMax = PlotPoints(2, i)
        If PlotPoints(2, i) < Ymin Then Ymin = PlotPoints(2, i)
        If PlotPoints(3, i) > ZMax Then ZMax = PlotPoints(3, i)
        If PlotPoints(3, i) < Zmin Then Zmin = PlotPoints(3, i)
    Next i
    Xorigin = Xmin + (XMax - Xmin) / 2
    Yorigin = Ymin + (YMax - Ymin) / 2
    Zorigin = Zmin + (ZMax - Zmin) / 2
    FindOrigin = False
End If

Select Case Index
    Case 0, 1  'xy plan view
        If optRotate(0) Then 'horizontal rotation
            If Option3 Then
                MDImain.ShifTurn RotateAnglePlan, Shift, Xorigin, Yorigin, PlotShiftRotate
            Else
                MDImain.ShifTurn RotateAnglePlan, Shift, Text4(0), Text4(1), PlotShiftRotate
            End If
            CurrentAction = RotateAnglePlan
            ViewIndex = 0
        Else 'vertical rotation
            MDImain.ShifTurn RotateAngleSide, Shift, Yorigin, Zorigin, PlotShiftRotate
            CurrentAction = RotateAngleSide
            ViewIndex = 1
        End If
    Case 2, 3 'yz side view
        If optRotate(0) Then 'horizontal rotation
            MDImain.ShifTurn RotateAngleSide, Shift, Yorigin, Zorigin, PlotShiftRotate
            CurrentAction = RotateAngleSide
            ViewIndex = 1
        Else
            MDImain.ShifTurn RotateAngleFront, Shift, Xorigin, Zorigin, PlotShiftRotate
            CurrentAction = RotateAngleFront
            ViewIndex = 2
        End If
    Case 4, 5 'xz side view
        If optRotate(0) Then 'horizontal rotation
            MDImain.ShifTurn RotateAngleFront, Shift, Xorigin, Zorigin, PlotShiftRotate
            CurrentAction = RotateAngleFront
            ViewIndex = 2
        Else
            MDImain.ShifTurn RotateAngleSide, Shift, Yorigin, Zorigin, PlotShiftRotate
            CurrentAction = RotateAngleSide
            ViewIndex = 1
        End If
End Select

CumAngle(ViewIndex) = CumAngle(ViewIndex) + Shift
lblAngle(ViewIndex).Caption = Format(CumAngle(ViewIndex), "####0.000")

If Recording Then
    If CurrentAction = PreviousAction Then
        rstRecording.MoveLast
        TempShift = rstRecording("Shift")
        rstRecording.Edit
        rstRecording("Shift") = TempShift + Shift
        rstRecording.Update
    Else
        rstRecording.AddNew
        rstRecording("action") = CurrentAction
        rstRecording("Shift") = Shift
        PreviousAction = CurrentAction
'        Select Case Index
'            Case 0, 1
'                rstRecording("action") = RotateAnglePlan
'                rstRecording("Shift") = Shift
'                PreviousAction = RotateAnglePlan
'            Case 2, 3
'                rstRecording("action") = RotateAngleSide
'                rstRecording("shift") = Shift
'                PreviousAction = RotateAngleSide
'            Case 4, 5
'                rstRecording("action") = RotateAngleFront
'                rstRecording("shift") = Shift
'                PreviousAction = RotateAngleFront
'        End Select
        rstRecording.Update
    End If
End If
DataChanged = True

End Sub

Private Sub cmdUpDown_Click(Index As Integer)

Set OptionButton = optUpDown
GetIndices Index
If Not IsNumeric(txtUpDown(ViewIndex)) Then
    MsgBox ("Invalid (non-numeric characters) value for shift")
    Exit Sub
End If

Select Case Index
    Case 1, 3, 5
        Sign = -1
    Case Else
        Sign = 1
End Select

Shift = Val(txtUpDown(ViewIndex)) / OptionScale * Sign
CumUpDown(ViewIndex) = CumUpDown(ViewIndex) + Shift
lblUpDown(ViewIndex).Caption = Format(CumUpDown(ViewIndex), "####0.000")
Select Case Index
    Case 0, 1
        MDImain.ShifTurn ShiftUpDownPlan, Shift, 0, 0, PlotShiftRotate
        CurrentAction = ShiftUpDownPlan
    Case 2, 3
        MDImain.ShifTurn ShiftUpDownSide, Shift, 0, 0, PlotShiftRotate
        CurrentAction = ShiftUpDownSide
    Case 4, 5
        MDImain.ShifTurn ShiftUpDownFront, Shift, 0, 0, PlotShiftRotate
        CurrentAction = ShiftUpDownFront
End Select

If Recording Then
    If CurrentAction = PreviousAction Then
        rstRecording.MoveLast
        TempShift = rstRecording("Shift")
        rstRecording.Edit
        rstRecording("Shift") = TempShift + Shift
        rstRecording.Update
    Else
        rstRecording.AddNew
        Select Case Index
            Case 0, 1
                rstRecording("action") = ShiftUpDownPlan
                rstRecording("Shift") = Shift
                PreviousAction = ShiftUpDownPlan
            Case 2, 3
                rstRecording("action") = ShiftUpDownSide
                rstRecording("shift") = Shift
                PreviousAction = ShiftUpDownSide
            Case 4, 5
                rstRecording("action") = ShiftUpDownFront
                rstRecording("shift") = Shift
                PreviousAction = ShiftUpDownFront
        End Select
        rstRecording.Update
        
    End If
End If
FindOrigin = True
DataChanged = True
Set OptionButton = Nothing

End Sub

Private Sub Command4_Click()

response = MsgBox("This will permanently change data in the XYZ table.  Continue anyway?", vbYesNo)
If response = vbNo Then
    Exit Sub
End If
Screen.MousePointer = 11
MDImain.ShifTurn WriteData, 0, 0, 0, PlotShiftRotate
Screen.MousePointer = 1

DataChanged = False

End Sub

Private Sub Command5_Click()

MDImain.ShifTurn ResetData, 0, 0, 0, PlotShiftRotate
DataChanged = False
For i = 0 To 2
    CumUpDown(i) = 0
    lblUpDown(i) = Format(0, "####0.000")
    CumLeftRight(i) = 0
    lblLeftRight(i) = Format(0, "####0.000")
    CumAngle(i) = 0
    lblAngle(i) = Format(0, "####0.000")
    txtUpDown(i) = 1
    txtLeftRight(i) = 1
    txtAngle(i) = 1
Next i
If Recording Then
    Cancelling = True
    cmdRecord_Click
    Cancelling = False
End If
lstRotations.ListIndex = -1

End Sub

Private Sub Command6_Click()
'If DataChanged Then
'    response = MsgBox("Save changes?", vbYesNo)
'    If response = vbYes Then
'        Command4_Click
'    End If
'End If

Command5_Click
Unload Me
End Sub

Private Sub Command8_Click()

Dim DeltaDatum As Single

If SmallDatum Then
    DeltaDatum = 0.25
    SmallDatum = False
Else
    DeltaDatum = 4
    SmallDatum = True
End If

If MDImain.OverlayPlotDatums.Checked Then
    MDImain.OverlayPlotDatums_Click
    On Error Resume Next
    For i = 1 To nDatumPoints
        Unload CurrentPF.shpDatum(i)
    Next i
    On Error GoTo 0
    CurrentPF.shpDatum(0).height = CurrentPF.shpDatum(0).height / DeltaDatum
    CurrentPF.shpDatum(0).Width = CurrentPF.shpDatum(0).Width / DeltaDatum
    
    MDImain.OverlayPlotDatums_Click
Else
    CurrentPF.shpDatum(0).height = CurrentPF.shpDatum(0).height / DeltaDatum
    CurrentPF.shpDatum(0).Width = CurrentPF.shpDatum(0).Width / DeltaDatum
End If
CurrentPF.Form_Paint

End Sub

Private Sub Datum_GotFocus(Index As Integer)

Datum(0).BackColor = QBColor(15)
Datum(1).BackColor = QBColor(15)
Datum(2).BackColor = QBColor(15)
Datum(Index).BackColor = QBColor(14)

SendKeys "{F4}", True

End Sub

Private Sub Form_Load()

DoFormSettings Me, GetSettings
Me.height = 8500
Me.Width = 14385

Dim temparray(100) As String
Dim nelements As Integer
Dim A As Integer
Dim flag As Boolean

'lstrotations.Clear
'ReDim Inidata(1, 2)
'iniclass = "[SHIFTROTATE]"
'IniFile = dbINIfile
'Screen.MousePointer = 11
'
'
'Inidata(1, 1) = "RotationName"
'Call ReadIni(IniFile, iniclass, Inidata(), Status)
'ParseINIline Inidata(1, 2), RotationName(), nRotationNames
'For A = 1 To nRotationNames
'    lstrotations.AddItem RotationName(A)
'Next A
'cmdDeleteRotation.Enabled = False


''' start shannon code
Dim db As Database
Datum(0).Clear
Datum(1).Clear
Datum(2).Clear
For A = 1 To nDatumPoints
    Datum(0).AddItem DatumName(A)
    Datum(1).AddItem DatumName(A)
    Datum(2).AddItem DatumName(A)
Next A
Datum(0).ListIndex = 0 'better will be to save these as defaults in the ini file
Datum(1).ListIndex = 1
Datum(2).ListIndex = 2

sqlString = "SELECT [wbdata_" + CurrentWorkBookName + "].Unit, [wbdata_" + CurrentWorkBookName + "].ID,"
sqlString = sqlString + " Context.level, Context.code, suffix, x, y, z"
sqlString = sqlString + " FROM [wbdata_" + CurrentWorkBookName + "] LEFT JOIN Context ON ([wbdata_" + CurrentWorkBookName + "].ID = Context.ID) AND ([wbdata_" + CurrentWorkBookName + "].Unit = Context.Unit)"

Set db = DBEngine.OpenDatabase(MDImain.MainFileName)
Set plotted_points_db.Recordset = db.OpenRecordset(sqlString)
plotted_points_db.Refresh

plotted_points_db.Recordset.MoveFirst
Do Until plotted_points_db.Recordset.EOF
    matching_datum(0).AddItem RTrim(plotted_points_db.Recordset(0).Value) + "-" + LTrim(plotted_points_db.Recordset(1).Value) + "(" + LTrim(LTrim(plotted_points_db.Recordset(4).Value)) + ")"
    matching_datum(1).AddItem RTrim(plotted_points_db.Recordset(0).Value) + "-" + LTrim(plotted_points_db.Recordset(1).Value) + "(" + LTrim(LTrim(plotted_points_db.Recordset(4).Value)) + ")"
    matching_datum(2).AddItem RTrim(plotted_points_db.Recordset(0).Value) + "-" + LTrim(plotted_points_db.Recordset(1).Value) + "(" + LTrim(LTrim(plotted_points_db.Recordset(4).Value)) + ")"
    plotted_points_db.Recordset.MoveNext
Loop

matching_datum(0).ListIndex = -1
matching_datum(1).ListIndex = -1
matching_datum(2).ListIndex = -1
matching_datum(0).Text = ""
matching_datum(1).Text = ""
matching_datum(2).Text = ""
Datum(0).BackColor = QBColor(15)
Datum(1).BackColor = QBColor(15)
Datum(2).BackColor = QBColor(15)

plotted_points_db.Recordset.MoveFirst
''' end shannon code

GetRotations
cmdDeleteRotation.Enabled = False

Select Case PlotView
    Case "XY"
        SetDirection 0
    Case "YZ"
        SetDirection 1
    Case "XZ"
        SetDirection 2
End Select

If CurrentNpoint > 0 Then
    X1 = 0
    Y1 = 0
    Z1 = 0
    X2 = 0
    Y2 = 0
    Z2 = 0
    If PlotPoints(4, CurrentNpoint) = 1 Then
        If CurrentNpoint = nRecords Then
            X1 = PlotPoints(PlotX, CurrentNpoint)
            Y1 = PlotPoints(PlotY, CurrentNpoint)
            Z1 = PlotPoints(PlotZ, CurrentNpoint)
            X2 = PlotPoints(PlotX, CurrentNpoint - 1)
            Y2 = PlotPoints(PlotY, CurrentNpoint - 1)
            Z2 = PlotPoints(PlotZ, CurrentNpoint - 1)
        ElseIf PlotPoints(4, CurrentNpoint + 1) = 0 Then
            X1 = PlotPoints(PlotX, CurrentNpoint)
            Y1 = PlotPoints(PlotY, CurrentNpoint)
            Z1 = PlotPoints(PlotZ, CurrentNpoint)
            X2 = PlotPoints(PlotX, CurrentNpoint - 1)
            Y2 = PlotPoints(PlotY, CurrentNpoint - 1)
            Z2 = PlotPoints(PlotZ, CurrentNpoint - 1)
        End If
    Else
        If CurrentNpoint = nRecords Then
        ElseIf nRecords = CurrentNpoint + 1 Then
            If PlotPoints(4, CurrentNpoint + 1) = 1 Then
                X1 = PlotPoints(PlotX, CurrentNpoint)
                Y1 = PlotPoints(PlotY, CurrentNpoint)
                Z1 = PlotPoints(PlotZ, CurrentNpoint)
                X2 = PlotPoints(PlotX, CurrentNpoint + 1)
                Y2 = PlotPoints(PlotY, CurrentNpoint + 1)
                Z2 = PlotPoints(PlotZ, CurrentNpoint + 1)
            End If
        ElseIf PlotPoints(4, CurrentNpoint + 1) = 1 And PlotPoints(4, CurrentPoint + 2) = 0 Then
            X1 = PlotPoints(PlotX, CurrentNpoint)
            Y1 = PlotPoints(PlotY, CurrentNpoint)
            Z1 = PlotPoints(PlotZ, CurrentNpoint)
            X2 = PlotPoints(PlotX, CurrentNpoint + 1)
            Y2 = PlotPoints(PlotY, CurrentNpoint + 1)
            Z2 = PlotPoints(PlotZ, CurrentNpoint + 1)
        End If
    End If
    If X1 <> X2 Or Y1 <> Y2 Or Z1 <> Z2 Then
        Call frmOrientations.calcnewstrikeangle(X1, Y1, Z1, X2, Y2, Z2, sa)
        xyangle.Caption = "XY Angle = " + Format(sa, "###.##")
        Call frmOrientations.calcnewstrikeangle(Y1, Z1, 0, Y2, Z2, 0, sa)
        yzangle.Caption = "YZ Angle = " + Format(sa, "###.##")
        Call frmOrientations.calcnewstrikeangle(X1, Z1, 0, X2, Z2, 0, sa)
        xzangle.Caption = "XZ Angle = " + Format(sa, "###.##")
    End If
End If
Xorigin = PlotMinX + (PlotMaxX - PlotMinX) / 2
Yorigin = PlotMinY + (PlotMaxY - PlotMinY) / 2
Zorigin = PlotMinZ + (PlotMaxZ - PlotMinZ) / 2


'   C = (P1+P2+P3)/3 = ((x1+x2+x3)/3,(y1+y2+y3)/3,(z1+z2+z3)/3)
SmallDatum = False
ShiftRotateShowing = True
Recording = False
PlotShiftRotate = True
Screen.MousePointer = 1

End Sub

Private Sub Form_Unload(Cancel As Integer)

DoFormSettings Me, PutSettings
If SmallDatum Then
    Command8_Click
End If
Set rstRecording = Nothing
ShiftRotateShowing = False

End Sub

Private Sub lstRotations_Click()

cmdApplyRotation.Enabled = True
cmdDeleteRotation.Enabled = True

End Sub

Private Sub matching_datum_Click(Index As Integer)

matching_datum(Index).Tag = matching_datum(Index).Index

End Sub

Private Sub matching_datum_GotFocus(Index As Integer)

SendKeys "{F4}", True
  
End Sub

Private Sub Option4_Click()

If Option4 Then
    Label3(0).Visible = True
    Text4(0).Visible = True
    Label3(1).Visible = True
    Text4(1).Visible = True
Else
    Label3(0).Visible = False
    Text4(0).Visible = False
    Label3(1).Visible = False
    Text4(1).Visible = False
End If

End Sub

Public Sub SetDirection(Direction As Integer)

For i = 0 To 5
    cmdUpDown(i).Enabled = False
    cmdLeftRight(i).Enabled = False
    cmdRotate(i).Enabled = False
Next i
Select Case Direction
    Case 0
        Label15 = "X-Y (Plan) View"
        For i = 0 To 1
            cmdUpDown(i).Enabled = True
            cmdLeftRight(i).Enabled = True
            cmdRotate(i).Enabled = True
        Next i
    Case 1
        Label15 = "X-Z (Side) View"
        For i = 2 To 3
            cmdUpDown(i).Enabled = True
            cmdLeftRight(i).Enabled = True
            cmdRotate(i).Enabled = True
        Next i
    
    Case 2
        Label15 = "Y-Z (Front) View"
        For i = 4 To 5
            cmdUpDown(i).Enabled = True
            cmdLeftRight(i).Enabled = True
            cmdRotate(i).Enabled = True
        Next i
End Select
    
End Sub

Public Sub GetIndices(Index As Integer)

OptionScale = 1
Select Case Index
    Case 0, 1
        ViewIndex = 0
        If OptionButton(1) Then
            OptionScale = 100
        ElseIf OptionButton(2) Then
            OptionScale = 1000
        End If
    Case 2, 3
        ViewIndex = 1
        If OptionButton(4) Then
            OptionScale = 100
        ElseIf OptionButton(5) Then
            OptionScale = 1000
        End If
    Case 4, 5
        ViewIndex = 2
        If OptionButton(7) Then
            OptionScale = 100
        ElseIf OptionButton(8) Then
            OptionScale = 1000
        End If
End Select

End Sub

Public Sub GetRotations()

MDImain.MainDB.TableDefs.Refresh

lstRotations.Clear
Dim tdTemp As TableDef
For Each tdTemp In MDImain.MainDB.TableDefs
    If UCase(Left(tdTemp.name, 4)) = "RSR_" Then
        lstRotations.AddItem Mid(tdTemp.name, 5)
    End If
Next

End Sub

Private Sub plotted_points_grid_RowColChange(LastRow As Variant, ByVal LastCol As Integer)

Dim datum_no As Integer
datum_no = -1

If Datum(0).BackColor <> QBColor(15) Then datum_no = 0
If Datum(1).BackColor <> QBColor(15) Then datum_no = 1
If Datum(2).BackColor <> QBColor(15) Then datum_no = 2

If datum_no <> -1 Then
    matching_datum(datum_no).Text = RTrim(plotted_points_db.Recordset(0).Value) + "-" + LTrim(plotted_points_db.Recordset(1).Value) + "(" + LTrim(plotted_points_db.Recordset(4).Value) + ")"
    matching_datum(datum_no).Tag = plotted_points_db.Recordset.AbsolutePosition
End If

End Sub

Private Sub rotate_Click()

If matching_datum(0).Text = "" Or matching_datum(1).Text = "" Or matching_datum(2).Text = "" Then
    MsgBox "Selecting matching datums before rotating.", vbInformation
    Exit Sub
End If

If matching_datum(0).Text = matching_datum(1).Text Or matching_datum(0).Text = matching_datum(2).Text Or matching_datum(1).Text = matching_datum(2).Text Then
    MsgBox "Select three independent points as the matching datums.", vbInformation
    Exit Sub
End If

If Datum(0).Text = Datum(1).Text Or Datum(0).Text = Datum(2).Text Or Datum(1).Text = Datum(2).Text Then
    MsgBox "Select three independent datums points.", vbInformation
    Exit Sub
End If

'Convert datums to a triangle format
Dim destination(0 To 2) As Point
destination(0) = set_datum_point(Datum(0).Index + 1, DatumPoints())
destination(1) = set_datum_point(Datum(1).Index + 1, DatumPoints())
destination(2) = set_datum_point(Datum(2).Index + 1, DatumPoints())

'Convert source to a triangle format
Dim Source(0 To 2) As Point
Source(0) = set_plotted_point(Int(matching_datum(0).Tag) + 1, PlotPoints())
Source(1) = set_plotted_point(Int(matching_datum(1).Tag) + 1, PlotPoints())
Source(2) = set_plotted_point(Int(matching_datum(2).Tag) + 1, PlotPoints())

' Make a copy of the points to work with
Dim temp_points() As Point
temp_points = copy_points(PlotPoints())

' Two vectors to define where things are and where we want them to be
Dim source_vector As Point
Dim destination_vector As Point

' First line up one side of the triangle fromed by the three datum points
source_vector = normalize_vector(vector_subtract(Source(1), Source(0)))
destination_vector = normalize_vector(vector_subtract(destination(1), destination(0)))
temp_points = rotate_points(destination_vector, source_vector, temp_points)

' Now line up on the other side of the triangle formed by the three datum points
source_vector = normalize_vector(vector_subtract(temp_points(Int(matching_datum(2).Tag) + 1), temp_points(Int(matching_datum(0).Tag) + 1)))
destination_vector = normalize_vector(vector_subtract(destination(2), destination(0)))
temp_points = rotate_points(destination_vector, source_vector, temp_points)

' Now align the starting points of each grid systems by shifting the first datum points onto each other
Dim datum_diff As Point
datum_diff = vector_subtract(destination(0), temp_points(Int(matching_datum(0).Tag) + 1))
temp_points = translate_points(datum_diff, temp_points())

' All done so now put the points back in the main plot array
Call put_points_back(temp_points())

' And redraw everything
reset_scale
MDImain.ChangingScale = True
MDImain.PlotAll

End Sub

Private Function copy_points(pin() As Double) As Point()

Dim i As Integer
Dim pout(1 To 10000) As Point

For i = 1 To nRecords
    pout(i) = set_plotted_point(i, PlotPoints())
Next i

copy_points = pout

End Function

Private Sub put_points_back(pin() As Point)

Dim i As Integer

For i = 1 To nRecords
    PlotPoints(1, i) = pin(i).X
    PlotPoints(2, i) = pin(i).Y
    PlotPoints(3, i) = pin(i).z
Next i

End Sub

Private Sub reset_scale()

' Do some work to figure out how to plot the new points
Dim MinX As Single
Dim MaxX As Single
Dim MinY As Single
Dim MaxY As Single
Dim minz As Single
Dim maxz As Single
MinX = 9932000
MinY = 9932000
minz = 9932000
MaxX = -9932000
MaxY = -9932000
maxz = -9932000

Dim i As Integer

For i = 1 To nRecords
    If PlotPoints(1, i) <> 0 Or PlotPoints(2, i) <> 0 Or PlotPoints(3, i) <> 0 Then
        If PlotPoints(1, i) < MinX Then MinX = PlotPoints(1, i)
        If PlotPoints(1, i) > MaxX Then MaxX = PlotPoints(1, i)
        If PlotPoints(2, i) < MinY Then MinY = PlotPoints(2, i)
        If PlotPoints(2, i) > MaxY Then MaxY = PlotPoints(2, i)
        If PlotPoints(3, i) < minz Then minz = PlotPoints(3, i)
        If PlotPoints(3, i) > maxz Then maxz = PlotPoints(3, i)
    End If
Next i

If MinX < PlotMinX Then PlotMinX = MinX
If MaxX > PlotMaxX Then PlotMaxX = MaxX
If MinY < PlotMinY Then PlotMinY = MinY
If MaxY > PlotMaxY Then PlotMaxY = MaxY
If minz < PlotMinZ Then PlotMinZ = minz
If maxz > PlotMaxZ Then PlotMaxZ = maxz

ViewMinX = PlotMinX
ViewMaxX = PlotMaxX
ViewMinY = PlotMinY
ViewMaxY = PlotMaxY
ViewMinZ = PlotMinZ
ViewMaxZ = PlotMaxZ

End Sub

Private Function rotate_points(Source As Point, destination As Point, points_to_rotate() As Point) As Point()

' Make the rotation matrix from the source and destination vectors
Dim i() As Single
Dim vx(0 To 2, 0 To 2) As Single
Dim v2x() As Single
Dim v As Point
Dim s As Single
Dim c As Single

i = identity_matrix()

v = cross_product(Source, destination)
s = vector_magnitude(v)
c = dot_product(Source, destination)

vx(0, 0) = 0
vx(0, 1) = -1 * v.z
vx(0, 2) = v.Y

vx(1, 0) = v.z
vx(1, 1) = 0
vx(1, 2) = -1 * v.X

vx(2, 0) = -v.Y
vx(2, 1) = v.X
vx(2, 2) = 0

v2x = scale_matrix(1 / (1 + c), matrix_product(vx(), vx()))

' Now create the rotation matrix by adding these components
Dim r() As Single
r = matrix_add(i, vx)
r = matrix_add(r, v2x)

' Now do the rotation by multiplying this rotation matrix by the individual points (or vectors)
Dim xyz As Integer
Dim b As Integer

Dim rotated_points(1 To 10000) As Point

For b = 1 To nRecords
    rotated_points(b).X = (points_to_rotate(b).X * r(0, 0)) + (points_to_rotate(b).Y * r(1, 0)) + (points_to_rotate(b).z * r(2, 0))
    rotated_points(b).Y = (points_to_rotate(b).X * r(0, 1)) + (points_to_rotate(b).Y * r(1, 1)) + (points_to_rotate(b).z * r(2, 1))
    rotated_points(b).z = (points_to_rotate(b).X * r(0, 2)) + (points_to_rotate(b).Y * r(1, 2)) + (points_to_rotate(b).z * r(2, 2))
Next b

rotate_points = rotated_points

End Function

Private Function translate_points(point_translation As Point, points_to_translate() As Point) As Point()

Dim i As Integer
Dim translated_points(1 To 10000) As Point

For i = 1 To nRecords
    translated_points(i).X = points_to_translate(i).X + point_translation.X
    translated_points(i).Y = points_to_translate(i).Y + point_translation.Y
    translated_points(i).z = points_to_translate(i).z + point_translation.z
Next i

translate_points = translated_points

End Function

Function empty_matrix() As Single()

Dim A As Integer
Dim b As Integer
Dim i(0 To 2, 0 To 2) As Single

For A = 0 To 2
    For b = 0 To 2
        i(A, b) = 0
    Next b
Next A

empty_matrix = i

End Function

Function identity_matrix() As Single()

Dim A As Integer
Dim b As Integer
Dim i(0 To 2, 0 To 2) As Single

For A = 0 To 2
    For b = 0 To 2
        If A = b Then
            i(A, b) = 1
        Else
            i(A, b) = 0
        End If
    Next b
Next A

identity_matrix = i

End Function

Function matrix_product(A() As Single, b() As Single) As Single()

Dim row As Integer
Dim col As Integer
Dim Index As Integer
Dim c(0 To 2, 0 To 2) As Single

For row = 0 To 2
    For col = 0 To 2
        c(row, col) = 0
        For Index = 0 To 2
                c(row, col) = c(row, col) + A(row, Index) * b(Index, col)
        Next Index
    Next col
Next row

matrix_product = c

End Function

Private Function vector_magnitude(A As Point) As Single

vector_magnitude = Sqr(dot_product(A, A))

End Function

Private Function set_plotted_point(Index As Integer, points() As Double) As Point
    
    set_plotted_point.X = points(1, Index)
    set_plotted_point.Y = points(2, Index)
    set_plotted_point.z = points(3, Index)

End Function

Private Function set_datum_point(Index As Integer, points() As Double) As Point
    
    set_datum_point.X = points(Index, 1)
    set_datum_point.Y = points(Index, 2)
    set_datum_point.z = points(Index, 3)

End Function

Private Function surface_normal(a_triangle() As Point) As Point

Dim U As Point
Dim v As Point
Dim sn As Point

U = vector_subtract(a_triangle(1), a_triangle(0))
v = vector_subtract(a_triangle(2), a_triangle(0))

sn = cross_product(U, v)

surface_normal = normalize_vector(sn)

End Function

Private Function vector_subtract(p2 As Point, p1 As Point) As Point

Dim p As Point

p.X = p2.X - p1.X
p.Y = p2.Y - p1.Y
p.z = p2.z - p1.z

vector_subtract = p

End Function

Private Function normalize_vector(A As Point) As Point
        
Dim Length As Single

If Sqr(dot_product(A, A)) <> 0 Then normalize_vector = scale_vector(1 / Sqr(dot_product(A, A)), A)

End Function

Private Function dot_product(A As Point, b As Point) As Single
        
dot_product = A.X * b.X + A.Y * b.Y + A.z * b.z

End Function

Private Function scale_vector(scalar As Single, A As Point) As Point
        
scale_vector.X = scalar * A.X
scale_vector.Y = scalar * A.Y
scale_vector.z = scalar * A.z
'V2(W) = 1

End Function

Private Function scale_matrix(scalar As Single, m() As Single) As Single()

Dim A As Integer
Dim b As Integer
Dim r() As Single

r = empty_matrix()

For A = 0 To 2
    For b = 0 To 2
        r(A, b) = m(A, b) * scalar
    Next b
Next A

scale_matrix = r

End Function

Private Function cross_product(v1 As Point, v2 As Point) As Point
    
cross_product.X = v1.Y * v2.z - v1.z * v2.Y
cross_product.Y = v1.z * v2.X - v1.X * v2.z
cross_product.z = v1.X * v2.Y - v1.Y * v2.X
'C(W) = 1

End Function

Private Function matrix_add(m1() As Single, m2() As Single) As Single()

Dim A As Integer
Dim b As Integer
Dim r() As Single

r = empty_matrix()

For A = 0 To 2
    For b = 0 To 2
        r(A, b) = m1(A, b) + m2(A, b)
    Next b
Next A

matrix_add = r

End Function

