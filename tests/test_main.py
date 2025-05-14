import pytest
import os
import tempfile
import sys
from io import StringIO
from typing import List, Dict, Any

from main import (
    parse_arguments,
    read_csv,
    Report,
    PayoutReport,
    ReportsData,
    main
)

def test_parse_arguments(monkeypatch):

    test_args = ["main.py", "file1.csv", "file2.csv", "--report", "payout"]
    monkeypatch.setattr(sys, 'argv', test_args)
    result = parse_arguments()
    assert result[0] == "payout"
    assert result[1] == ["file1.csv", "file2.csv"]

def test_read_csv():
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv') as temp:
        temp.write("id,email,name,department,hours_worked,hourly_rate\n")
        temp.write("1,alice@example.com,Alice Johnson,Marketing,160,50\n")
        temp.write("2,bob@example.com,Bob Smith,Design,150,40\n")
        temp_name = temp.name
    
    try:
        data = read_csv(temp_name)
        assert len(data) == 2
        assert data[0]['name'] == 'Alice Johnson'
        assert data[0]['hours_worked'] == '160'
        assert data[0]['hourly_rate'] == '50'
        assert data[1]['name'] == 'Bob Smith'
    finally:
        os.unlink(temp_name)

def test_read_csv_empty_file():
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv') as temp:
        temp_name = temp.name
    
    try:
        data = read_csv(temp_name)
        assert len(data) == 0
    finally:
        os.unlink(temp_name)

def test_payout_report_generate():
    data = [
        {'id': '1', 'email': 'alice@example.com', 'name': 'Alice Johnson', 'department': 'Marketing', 'hours_worked': '160', 'hourly_rate': '50'},
        {'id': '2', 'email': 'bob@example.com', 'name': 'Bob Smith', 'department': 'Design', 'hours_worked': '150', 'rate': '40'},
        {'id': '3', 'email': 'carol@example.com', 'name': 'Carol Williams', 'department': 'Design', 'hours_worked': '170', 'salary': '60'}
    ]
    
    report = PayoutReport()
    result = report.generate(data)
    
    assert 'departments' in result
    assert 'Marketing' in result['departments']
    assert 'Design' in result['departments']

    marketing = result['departments']['Marketing']
    assert marketing['total_hours'] == 160
    assert marketing['total_payout'] == 8000
    assert len(marketing['employees']) == 1
    
    design = result['departments']['Design']
    assert design['total_hours'] == 320
    assert design['total_payout'] == 16200
    assert len(design['employees']) == 2

def test_payout_report_format_output():
    report = PayoutReport()
    result = {
        'departments': {
            'Marketing': {
                'employees': [
                    {'name': 'Alice Johnson', 'hours': 160, 'rate': 50, 'payout': 8000}
                ],
                'total_hours': 160,
                'total_payout': 8000
            }
        }
    }
    
    output = report.format_output(result)
    assert 'name' in output
    assert 'hours' in output
    assert 'rate' in output
    assert 'payout' in output
    assert 'Marketing' in output
    assert 'Alice Johnson' in output
    assert '$8000' in output

def test_report_factory():
    report = ReportsData.get_report('payout')
    assert isinstance(report, PayoutReport)

    with pytest.raises(ValueError):
        ReportsData.get_report('non_existent_report')

def test_main_success(monkeypatch):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv') as temp:
        temp.write("id,email,name,department,hours_worked,hourly_rate\n")
        temp.write("1,alice@example.com,Alice Johnson,Marketing,160,50\n")
        temp_name = temp.name
    
    try:
        test_args = ["main.py", temp_name, "--report", "payout"]
        monkeypatch.setattr(sys, 'argv', test_args)
        
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        result = main()

        assert result == 0
        
        output = mystdout.getvalue()
        assert "Marketing" in output
        assert "Alice Johnson" in output
        
        sys.stdout = old_stdout
    finally:
        os.unlink(temp_name)

def test_main_file_not_found(monkeypatch):
    test_args = ["main.py", "non_existent_file.csv", "--report", "payout"]
    monkeypatch.setattr(sys, 'argv', test_args)

    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    
    result = main()

    assert result == 1

    output = mystdout.getvalue()
    assert "Ошибка: открытия файла" in output
    
    sys.stdout = old_stdout

def test_main_invalid_report(monkeypatch):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv') as temp:
        temp.write("id,email,name,department,hours_worked,hourly_rate\n")
        temp.write("1,alice@example.com,Alice Johnson,Marketing,160,50\n")
        temp_name = temp.name
    
    try:
        test_args = ["main.py", temp_name, "--report", "invalid_report"]
        monkeypatch.setattr(sys, 'argv', test_args)

        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        result = main()

        assert result == 1

        output = mystdout.getvalue()
        assert "Ошибка: Отчет invalid_report типа не найден" in output
        
        sys.stdout = old_stdout
    finally:
        os.unlink(temp_name)
