import React from 'react';
import logo from './logo.svg';
import './App.css';
import { Row, Col, Divider } from 'antd';
import { Typography, Form, DatePicker, Input, Button } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';


const { Title, Text } = Typography;
const style = { background: '#0092ff', padding: '8px 0' };

class App extends React.Component {
  componentDidMount() {
    const apiUrl = 'https://us-east1-poised-lens-267620.cloudfunctions.net/get-earnings-call-date?date=2020-07-24';
    fetch(apiUrl)
      .then((response) => response.json())
      .then((data) => console.log('This is your data', data));
  }
  render() {
    return (
      <div className="App">
        <Divider orientation="left" style={{ color: '#333', fontWeight: 'normal' }}>
          <Title>Earnings Date API</Title>
        </Divider>
        <Row justify="center">
          <Col span={16}>
            <Form.Item label="Url">
              <Text code>https://us-east1-poised-lens-267620.cloudfunctions.net/get-earnings-call-date?date=2020-07-24</Text>
            </Form.Item>
          </Col>
        </Row>
        <br></br>
        <Row justify="center">
          <Col span={8}>
            <Form.Item label="Date">
              <DatePicker />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="Ticker">
              <Input style={{ width: '70%' }}/>
            </Form.Item>
          </Col>
        </Row>
      </div>
    );
  }
}

export default App;
